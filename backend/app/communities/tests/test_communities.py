import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.auth.jwt import create_access_token
from app.main import app


async def _seed_admin(db_conn: AsyncConnection) -> dict:
    uid = uuid.uuid4()
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.users (id, handle, display_name, role) "
            "VALUES (:id, :h, :n, 'admin')"
        ),
        {"id": uid, "h": f"admin_{uuid.uuid4().hex[:6]}", "n": "Admin"},
    )
    await db_conn.commit()
    return {"id": uid, "token": create_access_token(user_id=uid, role="admin")}


async def _seed_member(db_conn: AsyncConnection) -> dict:
    uid = uuid.uuid4()
    await db_conn.execute(
        text(
            "INSERT INTO syntrix.users (id, handle, display_name, role) "
            "VALUES (:id, :h, :n, 'member')"
        ),
        {"id": uid, "h": f"user_{uuid.uuid4().hex[:6]}", "n": "User"},
    )
    await db_conn.commit()
    return {"id": uid, "token": create_access_token(user_id=uid, role="member")}


@pytest.mark.asyncio
async def test_list_communities_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/communities")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_community_requires_admin(db_conn: AsyncConnection):
    member = await _seed_member(db_conn)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/communities",
            json={"name": "Test", "slug": "test-comm"},
            cookies={"access_token": member["token"]},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_creates_community(db_conn: AsyncConnection):
    admin = await _seed_admin(db_conn)
    slug = f"comm-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/communities",
            json={"name": "My Community", "slug": slug, "color": "#5d2424"},
            cookies={"access_token": admin["token"]},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == slug
    assert data["color"] == "#5d2424"
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_join_and_leave(db_conn: AsyncConnection):
    admin = await _seed_admin(db_conn)
    member = await _seed_member(db_conn)
    slug = f"jl-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "JoinLeave", "slug": slug},
            cookies={"access_token": admin["token"]},
        )
        join_resp = await client.post(
            f"/api/communities/{slug}/join",
            cookies={"access_token": member["token"]},
        )
        assert join_resp.json()["status"] == "joined"

        leave_resp = await client.post(
            f"/api/communities/{slug}/leave",
            cookies={"access_token": member["token"]},
        )
        assert leave_resp.json()["status"] == "left"


@pytest.mark.asyncio
async def test_owner_cannot_leave(db_conn: AsyncConnection):
    admin = await _seed_admin(db_conn)
    slug = f"own-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "OwnerTest", "slug": slug},
            cookies={"access_token": admin["token"]},
        )
        resp = await client.post(
            f"/api/communities/{slug}/leave",
            cookies={"access_token": admin["token"]},
        )
    assert resp.status_code == 400
