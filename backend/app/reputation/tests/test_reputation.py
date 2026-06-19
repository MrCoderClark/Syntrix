import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.auth.jwt import create_access_token
from app.main import app
from app.reputation.engine import award_rep


async def _seed_user(db_conn: AsyncConnection, role: str = "member") -> dict:
    uid = uuid.uuid4()
    handle = f"rep_{uuid.uuid4().hex[:6]}"
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.users "
            "(id, handle, display_name, role) "
            "VALUES (:id, :h, :n, :r)"
        ),
        {"id": uid, "h": handle, "n": "RepUser", "r": role},
    )
    await db_conn.commit()
    return {
        "id": uid,
        "handle": handle,
        "token": create_access_token(user_id=uid, role=role),
    }


@pytest.mark.asyncio
async def test_award_rep_updates_user_reputation(
    db_conn: AsyncConnection, db_session: AsyncSession
):
    user = await _seed_user(db_conn)
    await award_rep(db_session, user["id"], "answer_upvoted")
    await db_session.commit()

    row = await db_conn.execute(
        text("SELECT reputation FROM syntrix.users WHERE id = :id"),
        {"id": user["id"]},
    )
    assert row.scalar_one() == 10


@pytest.mark.asyncio
async def test_award_rep_reverse_negates_delta(db_conn: AsyncConnection, db_session: AsyncSession):
    user = await _seed_user(db_conn)
    await award_rep(db_session, user["id"], "answer_upvoted")
    await award_rep(db_session, user["id"], "answer_upvoted", reverse=True)
    await db_session.commit()

    row = await db_conn.execute(
        text("SELECT reputation FROM syntrix.users WHERE id = :id"),
        {"id": user["id"]},
    )
    assert row.scalar_one() == 0


@pytest.mark.asyncio
async def test_reputation_api_returns_events(db_conn: AsyncConnection, db_session: AsyncSession):
    user = await _seed_user(db_conn)
    src_id = uuid.uuid4()
    await award_rep(db_session, user["id"], "question_upvoted", src_id)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/users/{user['handle']}/reputation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reputation"] == 5
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "question_upvoted"
    assert data["events"][0]["delta"] == 5


@pytest.mark.asyncio
async def test_badge_awarded_on_first_answer(db_conn: AsyncConnection, db_session: AsyncSession):
    user = await _seed_user(db_conn)

    comm_owner = await _seed_user(db_conn, role="admin")
    comm_id = uuid.uuid4()
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.communities "
            "(id, name, slug, description, color, owner_id) "
            "VALUES (:id, :n, :s, :d, :c, :oid)"
        ),
        {
            "id": comm_id,
            "n": "BadgeTest",
            "s": f"bt_{uuid.uuid4().hex[:6]}",
            "d": "test",
            "c": "#000",
            "oid": comm_owner["id"],
        },
    )
    q_author = await _seed_user(db_conn)
    q_id = uuid.uuid4()
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.posts "
            "(id, community_id, author_id, title, body_json, "
            "body_html, post_type) "
            "VALUES (:id, :cid, :aid, :t, :bj, :bh, 'question')"
        ),
        {
            "id": q_id,
            "cid": comm_id,
            "aid": q_author["id"],
            "t": "Test Q",
            "bj": "{}",
            "bh": "<p>test</p>",
        },
    )
    ans_id = uuid.uuid4()
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.answers "
            "(id, question_id, author_id, body_json, body_html) "
            "VALUES (:id, :qid, :aid, :bj, :bh)"
        ),
        {
            "id": ans_id,
            "qid": q_id,
            "aid": user["id"],
            "bj": "{}",
            "bh": "<p>answer</p>",
        },
    )
    await db_conn.commit()

    from app.reputation.badges import check_badges

    awarded = await check_badges(db_session, user["id"])
    await db_session.commit()

    badge_slugs = [b.slug for b in awarded]
    assert "first-answer" in badge_slugs

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/users/{user['handle']}/reputation")
    data = resp.json()
    assert any(b["badge"]["slug"] == "first-answer" for b in data["badges"])
