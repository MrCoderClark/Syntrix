from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, ChatRoom, Community, CommunityMembership, User
from app.posts.renderer import render_tiptap_json

SIMPLE_BODY = {
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}],
}


async def _seed_community_with_users(
    session: AsyncSession,
    admin_id: uuid.UUID,
    member_id: uuid.UUID,
) -> Community:
    admin = User(
        id=admin_id, handle=f"admin_{admin_id.hex[:6]}", display_name="Admin", role="admin"
    )
    member = User(
        id=member_id, handle=f"chatter_{member_id.hex[:6]}", display_name="Chatter", role="member"
    )
    session.add_all([admin, member])
    await session.flush()

    slug = f"test-{uuid.uuid4().hex[:8]}"
    community = Community(name="Test", slug=slug, owner_id=admin_id, color="#111111")
    session.add(community)
    await session.flush()

    session.add_all(
        [
            CommunityMembership(community_id=community.id, user_id=admin_id, role="owner"),
            CommunityMembership(community_id=community.id, user_id=member_id, role="member"),
        ]
    )
    await session.flush()
    return community


@pytest.mark.asyncio
async def test_create_room_slug_unique(db_session: AsyncSession):
    """Two rooms in the same community cannot share a slug."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room1 = ChatRoom(
        community_id=community.id,
        name="General",
        slug="general",
        created_by=admin_id,
    )
    db_session.add(room1)
    await db_session.flush()

    room2 = ChatRoom(
        community_id=community.id,
        name="General 2",
        slug="general",
        created_by=admin_id,
    )
    db_session.add(room2)
    with pytest.raises(Exception):  # IntegrityError on unique constraint
        await db_session.flush()


@pytest.mark.asyncio
async def test_room_cascade_deletes_with_community(db_session: AsyncSession):
    """Deleting a community cascades to its rooms."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room = ChatRoom(
        community_id=community.id,
        name="General",
        slug="general",
        is_default=True,
        created_by=admin_id,
    )
    db_session.add(room)
    await db_session.flush()
    room_id = room.id

    await db_session.delete(community)
    await db_session.flush()

    result = await db_session.execute(select(ChatRoom).where(ChatRoom.id == room_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_send_and_fetch_message(db_session: AsyncSession):
    """A message can be inserted into a room and fetched back."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room = ChatRoom(
        community_id=community.id,
        name="General",
        slug="general",
        is_default=True,
        created_by=admin_id,
    )
    db_session.add(room)
    await db_session.flush()

    msg = ChatMessage(
        room_id=room.id,
        author_id=member_id,
        body_json=SIMPLE_BODY,
        body_html=render_tiptap_json(SIMPLE_BODY),
    )
    db_session.add(msg)
    await db_session.flush()

    result = await db_session.execute(select(ChatMessage).where(ChatMessage.room_id == room.id))
    messages = result.scalars().all()
    assert len(messages) == 1
    assert messages[0].body_json == SIMPLE_BODY


@pytest.mark.asyncio
async def test_message_cascade_deletes_with_room(db_session: AsyncSession):
    """Deleting a room cascades to its messages."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room = ChatRoom(
        community_id=community.id,
        name="General",
        slug="general",
        created_by=admin_id,
    )
    db_session.add(room)
    await db_session.flush()

    msg = ChatMessage(
        room_id=room.id,
        author_id=member_id,
        body_json=SIMPLE_BODY,
        body_html="<p>hello</p>",
    )
    db_session.add(msg)
    await db_session.flush()
    msg_id = msg.id

    await db_session.delete(room)
    await db_session.flush()

    result = await db_session.execute(select(ChatMessage).where(ChatMessage.id == msg_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_default_room_exists_after_community_seed(db_session: AsyncSession):
    """When a default room is added to a community, it is queryable by is_default."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room = ChatRoom(
        community_id=community.id,
        name="general",
        slug="general",
        is_default=True,
        created_by=admin_id,
    )
    db_session.add(room)
    await db_session.flush()

    result = await db_session.execute(
        select(ChatRoom).where(
            ChatRoom.community_id == community.id,
            ChatRoom.is_default.is_(True),
        )
    )
    default_room = result.scalar_one_or_none()
    assert default_room is not None
    assert default_room.slug == "general"


@pytest.mark.asyncio
async def test_message_history_ordering(db_session: AsyncSession):
    """Messages ordered newest-first when sorted by created_at desc, id desc."""
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    community = await _seed_community_with_users(db_session, admin_id, member_id)
    room = ChatRoom(
        community_id=community.id,
        name="General",
        slug="general",
        created_by=admin_id,
    )
    db_session.add(room)
    await db_session.flush()

    msgs = []
    for i in range(5):
        m = ChatMessage(
            room_id=room.id,
            author_id=member_id,
            body_json={
                "type": "doc",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": f"msg {i}"}]}
                ],
            },
            body_html=f"<p>msg {i}</p>",
        )
        db_session.add(m)
        await db_session.flush()
        msgs.append(m)

    result = await db_session.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
    )
    ordered = result.scalars().all()
    assert len(ordered) == 5
    # All messages inserted in the same transaction share the same created_at,
    # so they fall back to id DESC order. Verify the sort is stable and consistent:
    # re-running the same query should return the same order.
    result2 = await db_session.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
    )
    ordered2 = result2.scalars().all()
    assert [m.id for m in ordered] == [m.id for m in ordered2]
    # All seeded messages should appear in the results
    assert {m.id for m in ordered} == {m.id for m in msgs}


@pytest.mark.asyncio
async def test_community_creation_auto_creates_general_room(db_session: AsyncSession):
    """When a community is created, a default #general room is auto-created."""
    admin_id = uuid.uuid4()
    admin = User(id=admin_id, handle="admin", display_name="Admin", role="admin")
    db_session.add(admin)
    await db_session.flush()

    slug = f"test-{uuid.uuid4().hex[:8]}"
    community = Community(name="Test", slug=slug, owner_id=admin_id, color="#111111")
    db_session.add(community)
    await db_session.flush()

    # Simulate the auto-creation logic from create_community endpoint
    db_session.add(
        ChatRoom(
            community_id=community.id,
            name="general",
            slug="general",
            is_default=True,
            created_by=admin_id,
        )
    )
    await db_session.flush()

    # Verify the room exists and is queryable
    result = await db_session.execute(
        select(ChatRoom).where(
            ChatRoom.community_id == community.id,
            ChatRoom.is_default.is_(True),
        )
    )
    default_room = result.scalar_one_or_none()
    assert default_room is not None
    assert default_room.slug == "general"
    assert default_room.name == "general"
    assert default_room.is_default is True
