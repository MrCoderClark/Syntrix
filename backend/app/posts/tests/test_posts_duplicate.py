from __future__ import annotations

import asyncio
import platform
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from app.auth.jwt import create_access_token
from app.db.engine import async_engine
from app.main import app

REP_THRESHOLD = 500

if platform.system() == "Windows":

    @pytest.fixture(scope="session")
    def event_loop_policy():
        return asyncio.WindowsSelectorEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _verify_engine_reachable():
    try:
        async with async_engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except Exception as exc:
        pytest.exit(
            f"Database not reachable. Check PG_* env vars and Supabase stack. Error: {exc!r}",
            returncode=2,
        )
    yield


@pytest_asyncio.fixture
async def db_conn() -> AsyncIterator[AsyncConnection]:
    async with async_engine.connect() as conn:
        await conn.exec_driver_sql("DEALLOCATE ALL")
        await conn.rollback()
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()


@pytest_asyncio.fixture
async def session(db_conn: AsyncConnection) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(bind=db_conn, expire_on_commit=False)
    async with session_maker() as s:
        yield s


@pytest.fixture
def make_token():
    """Return a factory that creates a JWT cookie value for a given user_id and role."""

    def _factory(user_id: uuid.UUID, role: str = "member") -> str:
        return create_access_token(user_id=user_id, role=role)

    return _factory


@pytest_asyncio.fixture
async def dup_setup(db_conn: AsyncConnection):
    """Create community, owner, two questions, and a high-rep / low-rep member.

    Inserts are committed on db_conn so the ASGI app (which uses its own
    connection) can see the rows, then the outer transaction rolls back after
    the test.
    """
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    lowrep_id = uuid.uuid4()
    comm_id = uuid.uuid4()

    for uid, handle, name, rep in [
        (owner_id, f"dupowner_{uuid.uuid4().hex[:6]}", "Dup Owner", 0),
        (member_id, f"highrep_{uuid.uuid4().hex[:6]}", "High Rep User", REP_THRESHOLD),
        (lowrep_id, f"lowrep_{uuid.uuid4().hex[:6]}", "Low Rep User", 10),
    ]:
        await db_conn.execute(
            text(
                "INSERT INTO syntrix.users (id, handle, display_name, role, reputation) "
                "VALUES (:id, :handle, :name, 'member', :rep)"
            ),
            {"id": uid, "handle": handle, "name": name, "rep": rep},
        )

    await db_conn.execute(
        text(
            "INSERT INTO syntrix.communities (id, slug, name, owner_id) "
            "VALUES (:id, :slug, :name, :owner)"
        ),
        {
            "id": comm_id,
            "slug": f"dupcomm_{uuid.uuid4().hex[:6]}",
            "name": "Dup Community",
            "owner": owner_id,
        },
    )

    for uid, role in [(owner_id, "owner"), (member_id, "member"), (lowrep_id, "member")]:
        await db_conn.execute(
            text(
                "INSERT INTO syntrix.community_memberships (id, community_id, user_id, role) "
                "VALUES (:id, :cid, :uid, :role)"
            ),
            {"id": uuid.uuid4(), "cid": comm_id, "uid": uid, "role": role},
        )

    q1_id = uuid.uuid4()
    q2_id = uuid.uuid4()
    body_json = (
        '{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"body"}]}]}'
    )
    for qid, title in [(q1_id, "Original question"), (q2_id, "Duplicate question")]:
        await db_conn.exec_driver_sql(
            "INSERT INTO syntrix.posts "
            "(id, community_id, author_id, title, body_json, body_html, post_type) "
            "VALUES (%s, %s, %s, %s, %s::jsonb, '<p>body</p>', 'question')",
            (str(qid), str(comm_id), str(owner_id), title, body_json),
        )

    await db_conn.commit()
    return {
        "community_id": comm_id,
        "owner_id": owner_id,
        "member_id": member_id,
        "lowrep_id": lowrep_id,
        "q1_id": q1_id,
        "q2_id": q2_id,
    }


@pytest.mark.asyncio()
async def test_owner_can_mark_duplicate(dup_setup, make_token):
    token = make_token(dup_setup["owner_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["duplicate_of_id"] == str(dup_setup["q1_id"])
    assert resp.json()["duplicate_of_title"] == "Original question"


@pytest.mark.asyncio()
async def test_high_rep_member_can_mark(dup_setup, make_token):
    token = make_token(dup_setup["member_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio()
async def test_low_rep_member_cannot_mark(dup_setup, make_token):
    token = make_token(dup_setup["lowrep_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio()
async def test_cannot_mark_self_as_duplicate(dup_setup, make_token):
    token = make_token(dup_setup["owner_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/posts/{dup_setup['q1_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
    assert resp.status_code == 400, resp.text


@pytest.mark.asyncio()
async def test_cannot_chain_duplicates(dup_setup, make_token):
    token = make_token(dup_setup["owner_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mark q2 as dup of q1
        resp = await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
        assert resp.status_code == 200, resp.text
        # Try to mark q1 as dup of q2 (which is now a duplicate itself)
        resp = await client.post(
            f"/api/posts/{dup_setup['q1_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q2_id"])},
            cookies={"access_token": token},
        )
    assert resp.status_code == 400, resp.text


@pytest.mark.asyncio()
async def test_unmark_duplicate(dup_setup, make_token):
    token = make_token(dup_setup["owner_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mark first
        await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
        # Unmark
        resp = await client.delete(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            cookies={"access_token": token},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["duplicate_of_id"] is None


@pytest.mark.asyncio()
async def test_get_post_includes_duplicate_fields(dup_setup, make_token):
    token = make_token(dup_setup["owner_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            f"/api/posts/{dup_setup['q2_id']}/mark-duplicate",
            json={"duplicate_of_id": str(dup_setup["q1_id"])},
            cookies={"access_token": token},
        )
        resp = await client.get(f"/api/posts/{dup_setup['q2_id']}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["duplicate_of_id"] == str(dup_setup["q1_id"])
    assert resp.json()["duplicate_of_title"] == "Original question"
