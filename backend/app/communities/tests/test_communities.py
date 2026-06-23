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


@pytest.mark.asyncio
async def test_private_community_hidden_from_list(db_conn: AsyncConnection):
    """Private communities do not appear in the public list."""
    admin = await _seed_admin(db_conn)
    pub_slug = f"pub-{uuid.uuid4().hex[:8]}"
    priv_slug = f"priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "Public Community", "slug": pub_slug},
            cookies={"access_token": admin["token"]},
        )
        await client.post(
            "/api/communities",
            json={"name": "Private Community", "slug": priv_slug, "is_private": True},
            cookies={"access_token": admin["token"]},
        )
        resp = await client.get("/api/communities")
    assert resp.status_code == 200
    slugs = {c["slug"] for c in resp.json()}
    assert pub_slug in slugs
    assert priv_slug not in slugs


@pytest.mark.asyncio
async def test_private_community_returns_404_to_non_member(db_conn: AsyncConnection):
    """Non-members cannot view a private community — they get 404."""
    admin = await _seed_admin(db_conn)
    member = await _seed_member(db_conn)
    priv_slug = f"priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "Secret Club", "slug": priv_slug, "is_private": True},
            cookies={"access_token": admin["token"]},
        )
        # Anonymous user gets 404
        anon_resp = await client.get(f"/api/communities/{priv_slug}")
        assert anon_resp.status_code == 404

        # Non-member authenticated user gets 404
        member_resp = await client.get(
            f"/api/communities/{priv_slug}",
            cookies={"access_token": member["token"]},
        )
        assert member_resp.status_code == 404


@pytest.mark.asyncio
async def test_private_community_visible_to_member(db_conn: AsyncConnection):
    """Members of a private community can view it."""
    admin = await _seed_admin(db_conn)
    priv_slug = f"priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "Secret Club", "slug": priv_slug, "is_private": True},
            cookies={"access_token": admin["token"]},
        )
        # Admin who created the community is an owner/member — should see it
        resp = await client.get(
            f"/api/communities/{priv_slug}",
            cookies={"access_token": admin["token"]},
        )
        assert resp.status_code == 200
        assert resp.json()["is_private"] is True


@pytest.mark.asyncio
async def test_join_private_community_blocked(db_conn: AsyncConnection):
    """Direct join to a private community returns 403."""
    admin = await _seed_admin(db_conn)
    member = await _seed_member(db_conn)
    priv_slug = f"priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/communities",
            json={"name": "Invite Only", "slug": priv_slug, "is_private": True},
            cookies={"access_token": admin["token"]},
        )
        resp = await client.post(
            f"/api/communities/{priv_slug}/join",
            cookies={"access_token": member["token"]},
        )
    assert resp.status_code == 403
    assert "invite" in resp.json()["detail"].lower()
