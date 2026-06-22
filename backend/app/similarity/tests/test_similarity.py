from __future__ import annotations

import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from app.main import app


async def _seed_community_with_questions(db_conn: AsyncConnection) -> dict:
    """Create a community with several questions for similarity testing."""
    owner_id = uuid.uuid4()
    handle = f"simuser_{uuid.uuid4().hex[:6]}"
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.users (id, handle, display_name, role) "
        "VALUES (%s, %s, %s, 'member')",
        (str(owner_id), handle, "Sim User"),
    )
    comm_id = uuid.uuid4()
    slug = f"testcomm-{uuid.uuid4().hex[:6]}"
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.communities (id, slug, name, owner_id) " "VALUES (%s, %s, %s, %s)",
        (str(comm_id), slug, "Test Community", str(owner_id)),
    )
    # Insert questions with distinct titles
    questions = [
        (
            "How do I configure Nginx reverse proxy?",
            "I need help setting up Nginx as a reverse proxy for my web application",
        ),
        (
            "Nginx reverse proxy configuration guide",
            "Looking for a step-by-step guide to configure Nginx reverse proxy",
        ),
        (
            "Setting up Docker containers on Ubuntu",
            "I want to run Docker containers on my Ubuntu server",
        ),
        (
            "Python asyncio best practices",
            "What are the best practices for writing async Python code?",
        ),
    ]
    q_ids = [uuid.uuid4() for _ in questions]
    rows = []
    for qid, (title, body) in zip(q_ids, questions, strict=False):
        body_doc = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}],
        }
        rows.append(
            (
                str(qid),
                str(comm_id),
                str(owner_id),
                title,
                json.dumps(body_doc),
                f"<p>{body}</p>",
            )
        )
    # Use executemany to insert all rows in one prepared-statement execution,
    # avoiding psycopg3 auto-prepare threshold across per-row loop calls.
    await db_conn.exec_driver_sql(
        "INSERT INTO syntrix.posts "
        "(id, community_id, author_id, title, body_json, body_html, post_type) "
        "VALUES (%s, %s, %s, %s, %s, %s, 'question')",
        rows,
    )
    await db_conn.commit()
    return {
        "community_id": comm_id,
        "slug": slug,
        "owner_id": owner_id,
        "question_ids": q_ids,
    }


@pytest.mark.asyncio
async def test_similar_by_title(db_conn: AsyncConnection):
    data = await _seed_community_with_questions(db_conn)
    slug = data["slug"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/communities/{slug}/questions/similar",
            params={"title": "How to configure Nginx reverse proxy"},
        )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    titles = [item["title"] for item in items]
    assert any("Nginx" in t for t in titles)


@pytest.mark.asyncio
async def test_similar_by_title_no_match(db_conn: AsyncConnection):
    data = await _seed_community_with_questions(db_conn)
    slug = data["slug"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/communities/{slug}/questions/similar",
            params={"title": "Quantum computing fundamentals"},
        )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 0


@pytest.mark.asyncio
async def test_similar_by_title_short_query(db_conn: AsyncConnection):
    data = await _seed_community_with_questions(db_conn)
    slug = data["slug"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/communities/{slug}/questions/similar",
            params={"title": "hi"},
        )
    assert resp.status_code == 422  # min_length=10


@pytest.mark.asyncio
async def test_similar_body_search(db_conn: AsyncConnection):
    data = await _seed_community_with_questions(db_conn)
    slug = data["slug"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/communities/{slug}/questions/similar",
            json={
                "title": "reverse proxy setup",
                "body_text": "I need to configure Nginx as a reverse proxy for my web application",
            },
        )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    titles = [item["title"] for item in items]
    assert any("Nginx" in t for t in titles)


@pytest.mark.asyncio
async def test_similar_nonexistent_community():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/communities/nosuchcomm/questions/similar",
            params={"title": "anything at all here"},
        )
    assert resp.status_code == 404
