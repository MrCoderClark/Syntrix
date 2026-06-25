from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatRoom, ChatRoomMember, Community, CommunityMembership, Invite, User


@pytest.fixture
def user_ids():
    return uuid.uuid4(), uuid.uuid4()


async def test_invite_unique_constraint(db_session: AsyncSession, user_ids):
    """Can't create duplicate pending invites for same target+user."""
    inviter_id, invitee_id = user_ids
    db_session.add_all(
        [
            User(
                id=inviter_id,
                handle=f"inv-{uuid.uuid4().hex[:6]}",
                display_name="Inviter",
                role="member",
            ),
            User(
                id=invitee_id,
                handle=f"tgt-{uuid.uuid4().hex[:6]}",
                display_name="Invitee",
                role="member",
            ),
        ]
    )
    await db_session.flush()

    target_id = uuid.uuid4()
    inv1 = Invite(
        target_type="room",
        target_id=target_id,
        invited_by=inviter_id,
        invited_user_id=invitee_id,
    )
    db_session.add(inv1)
    await db_session.flush()

    inv2 = Invite(
        target_type="room",
        target_id=target_id,
        invited_by=inviter_id,
        invited_user_id=invitee_id,
    )
    db_session.add(inv2)
    with pytest.raises(Exception):  # IntegrityError from unique constraint
        await db_session.flush()


async def test_accept_invite_creates_membership(db_session: AsyncSession, user_ids):
    """Accepting a community invite creates a CommunityMembership."""
    admin_id, invitee_id = user_ids
    db_session.add_all(
        [
            User(
                id=admin_id,
                handle=f"adm-{uuid.uuid4().hex[:6]}",
                display_name="Admin",
                role="admin",
            ),
            User(
                id=invitee_id,
                handle=f"tgt-{uuid.uuid4().hex[:6]}",
                display_name="Invitee",
                role="member",
            ),
        ]
    )
    await db_session.flush()

    community = Community(
        name="Private Club",
        slug=f"priv-{uuid.uuid4().hex[:8]}",
        owner_id=admin_id,
        color="#333",
        is_private=True,
    )
    db_session.add(community)
    await db_session.flush()

    db_session.add(CommunityMembership(community_id=community.id, user_id=admin_id, role="owner"))
    await db_session.flush()

    invite = Invite(
        target_type="community",
        target_id=community.id,
        invited_by=admin_id,
        invited_user_id=invitee_id,
    )
    db_session.add(invite)
    await db_session.flush()

    # Simulate acceptance
    invite.status = "accepted"
    db_session.add(
        CommunityMembership(community_id=community.id, user_id=invitee_id, role="member")
    )
    await db_session.flush()

    result = await db_session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.user_id == invitee_id,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_accept_room_invite_creates_room_member(db_session: AsyncSession, user_ids):
    """Accepting a room invite creates a ChatRoomMember."""
    owner_id, invitee_id = user_ids
    db_session.add_all(
        [
            User(
                id=owner_id,
                handle=f"own-{uuid.uuid4().hex[:6]}",
                display_name="Owner",
                role="member",
            ),
            User(
                id=invitee_id,
                handle=f"tgt-{uuid.uuid4().hex[:6]}",
                display_name="Invitee",
                role="member",
            ),
        ]
    )
    await db_session.flush()

    community = Community(
        name="Test",
        slug=f"test-{uuid.uuid4().hex[:8]}",
        owner_id=owner_id,
        color="#444",
    )
    db_session.add(community)
    await db_session.flush()

    room = ChatRoom(
        community_id=community.id,
        name="Secret",
        slug="secret",
        is_private=True,
        created_by=owner_id,
    )
    db_session.add(room)
    await db_session.flush()

    db_session.add(ChatRoomMember(room_id=room.id, user_id=owner_id, added_by=owner_id))
    await db_session.flush()

    invite = Invite(
        target_type="room",
        target_id=room.id,
        invited_by=owner_id,
        invited_user_id=invitee_id,
    )
    db_session.add(invite)
    await db_session.flush()

    # Simulate acceptance
    invite.status = "accepted"
    db_session.add(ChatRoomMember(room_id=room.id, user_id=invitee_id, added_by=owner_id))
    await db_session.flush()

    result = await db_session.execute(
        select(ChatRoomMember).where(
            ChatRoomMember.room_id == room.id,
            ChatRoomMember.user_id == invitee_id,
        )
    )
    assert result.scalar_one_or_none() is not None
