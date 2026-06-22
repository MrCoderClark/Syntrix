from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from app.auth.jwt import create_access_token
from app.main import app


async def _seed_user_and_post(db_conn: AsyncConnection) -> dict:
    user_id = uuid.uuid4()
    handle = f"voteuser_{uuid.uuid4().hex[:6]}"
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.users (id, handle, display_name, role) "
        "VALUES (%s, %s, %s, 'member')",
        (str(user_id), handle, "Vote User"),
    )
    comm_id = uuid.uuid4()
    slug = f"vc-{uuid.uuid4().hex[:6]}"
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.communities (id, slug, name, owner_id) " "VALUES (%s, %s, %s, %s)",
        (str(comm_id), slug, "Vote Community", str(user_id)),
    )
    # Create a second user as post author (can't vote on own post)
    author_id = uuid.uuid4()
    author_handle = f"author_{uuid.uuid4().hex[:6]}"
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.users (id, handle, display_name, role) "
        "VALUES (%s, %s, %s, 'member')",
        (str(author_id), author_handle, "Author User"),
    )
    post_id = uuid.uuid4()
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.posts (id, community_id, author_id, title, body_json, body_html) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            str(post_id),
            str(comm_id),
            str(author_id),
            "Test Post",
            '{"type":"doc","content":[]}',
            "<p></p>",
        ),
    )
    post_id_2 = uuid.uuid4()
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.posts (id, community_id, author_id, title, body_json, body_html) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            str(post_id_2),
            str(comm_id),
            str(author_id),
            "Test Post 2",
            '{"type":"doc","content":[]}',
            "<p></p>",
        ),
    )
    # Add membership for user
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.community_memberships (community_id, user_id) VALUES (%s, %s)",
        (str(comm_id), str(user_id)),
    )
    # Insert a vote: user upvoted post_id
    vote_id = uuid.uuid4()
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.post_votes (id, user_id, post_id, value) VALUES (%s, %s, %s, %s)",
        (str(vote_id), str(user_id), str(post_id), 1),
    )
    await db_conn.commit()
    return {
        "user_id": user_id,
        "handle": handle,
        "post_id": post_id,
        "post_id_2": post_id_2,
    }


@pytest.mark.asyncio
async def test_batch_votes_returns_existing_votes(db_conn: AsyncConnection):
    data = await _seed_user_and_post(db_conn)
    token = create_access_token(user_id=data["user_id"], role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/votes/mine",
            params={
                "target_type": "post",
                "target_ids": f"{data['post_id']},{data['post_id_2']}",
            },
            cookies={"access_token": token},
        )
    assert resp.status_code == 200
    votes = resp.json()["votes"]
    assert votes[str(data["post_id"])] == 1
    assert str(data["post_id_2"]) not in votes


@pytest.mark.asyncio
async def test_batch_votes_unauthenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/votes/mine",
            params={
                "target_type": "post",
                "target_ids": str(uuid.uuid4()),
            },
        )
    # Unauthenticated returns 401 (CurrentUser dependency)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_batch_votes_invalid_target_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/votes/mine",
            params={
                "target_type": "invalid",
                "target_ids": str(uuid.uuid4()),
            },
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_batch_votes_too_many_ids(db_conn: AsyncConnection):
    data = await _seed_user_and_post(db_conn)
    token = create_access_token(user_id=data["user_id"], role="member")
    ids = ",".join(str(uuid.uuid4()) for _ in range(51))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/votes/mine",
            params={"target_type": "post", "target_ids": ids},
            cookies={"access_token": token},
        )
    assert resp.status_code == 422
