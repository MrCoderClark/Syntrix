import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.auth.jwt import create_access_token
from app.main import app


async def _seed_user(db_conn: AsyncConnection, handle: str = "testuser") -> dict:
    user_id = uuid.uuid4()
    await db_conn.execute(
        text(
            """
            INSERT INTO users (id, handle, display_name, role)
            VALUES (:id, :handle, :name, 'member')
        """
        ),
        {"id": user_id, "handle": handle, "name": f"Test {handle}"},
    )
    await db_conn.commit()
    return {"id": user_id, "handle": handle}


@pytest.mark.asyncio
async def test_get_profile_by_handle(db_conn: AsyncConnection):
    user = await _seed_user(db_conn, "alice")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/users/{user['handle']}")
    assert resp.status_code == 200
    assert resp.json()["handle"] == "alice"


@pytest.mark.asyncio
async def test_get_profile_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/users/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_profile_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch("/api/users/me", json={"display_name": "New"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_display_name(db_conn: AsyncConnection):
    user = await _seed_user(db_conn, "bob")
    token = create_access_token(user_id=user["id"], role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/api/users/me",
            json={"display_name": "Bob Updated"},
            cookies={"access_token": token},
        )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Bob Updated"


@pytest.mark.asyncio
async def test_update_handle_rejects_invalid(db_conn: AsyncConnection):
    user = await _seed_user(db_conn, "charlie")
    token = create_access_token(user_id=user["id"], role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/api/users/me",
            json={"handle": "_bad_"},
            cookies={"access_token": token},
        )
    assert resp.status_code == 422
