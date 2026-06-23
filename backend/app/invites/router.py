from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models import (
    ChatRoom,
    ChatRoomMember,
    Community,
    CommunityMembership,
    Invite,
    User,
)
from app.redis import publish_event

from .schemas import CreateInviteRequest, InviteResponse

router = APIRouter(prefix="/api/invites", tags=["invites"])


def _invite_response(
    invite: Invite,
    *,
    target_name: str | None = None,
    inviter_handle: str | None = None,
) -> InviteResponse:
    return InviteResponse(
        id=invite.id,
        target_type=invite.target_type,
        target_id=invite.target_id,
        target_name=target_name,
        invited_by=invite.invited_by,
        invited_by_handle=inviter_handle,
        invited_user_id=invite.invited_user_id,
        status=invite.status,
        created_at=invite.created_at,
        responded_at=invite.responded_at,
    )


@router.post("", response_model=InviteResponse, status_code=201)
async def create_invite(
    body: CreateInviteRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if body.invited_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")

    target_user = await session.get(User, body.invited_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_name = None

    if body.target_type == "room":
        room = await session.get(ChatRoom, body.target_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        if not room.is_private:
            raise HTTPException(status_code=400, detail="Can only invite to private rooms")
        # Must be a room member to invite
        own_member = await session.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room.id,
                ChatRoomMember.user_id == user.id,
            )
        )
        if not own_member.scalar_one_or_none() and user.role != "admin":
            raise HTTPException(status_code=403, detail="Not a member of this room")
        target_name = room.name

    elif body.target_type == "community":
        community = await session.get(Community, body.target_id)
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        if not community.is_private:
            raise HTTPException(status_code=400, detail="Can only invite to private communities")
        # Must be mod/owner/admin to invite to community
        membership = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == community.id,
                CommunityMembership.user_id == user.id,
            )
        )
        mem = membership.scalar_one_or_none()
        if (not mem or mem.role not in ("mod", "owner")) and user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Only mods, owners, or admins can invite to communities"
            )
        target_name = community.name

    # Check for existing pending invite
    existing = await session.execute(
        select(Invite).where(
            Invite.target_type == body.target_type,
            Invite.target_id == body.target_id,
            Invite.invited_user_id == body.invited_user_id,
            Invite.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Invite already pending")

    invite = Invite(
        target_type=body.target_type,
        target_id=body.target_id,
        invited_by=user.id,
        invited_user_id=body.invited_user_id,
    )
    session.add(invite)
    await session.flush()

    resp = _invite_response(invite, target_name=target_name, inviter_handle=user.handle)

    await publish_event(
        f"syntrix:system:{body.invited_user_id}",
        "system.invited",
        resp.model_dump(mode="json"),
    )

    return resp


@router.get("/mine", response_model=list[InviteResponse])
async def my_invites(
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Invite, User)
        .outerjoin(User, Invite.invited_by == User.id)
        .where(
            Invite.invited_user_id == user.id,
            Invite.status == "pending",
        )
        .order_by(Invite.created_at.desc())
    )

    items = []
    for row in result.all():
        invite = row.Invite
        inviter = row.User

        target_name = None
        if invite.target_type == "room":
            room = await session.get(ChatRoom, invite.target_id)
            target_name = room.name if room else None
        elif invite.target_type == "community":
            community = await session.get(Community, invite.target_id)
            target_name = community.name if community else None

        items.append(
            _invite_response(
                invite,
                target_name=target_name,
                inviter_handle=inviter.handle if inviter else None,
            )
        )
    return items


@router.post("/{invite_id}/accept", response_model=InviteResponse)
async def accept_invite(
    invite_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    invite = await session.get(Invite, invite_id)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.invited_user_id != user.id:
        raise HTTPException(status_code=403, detail="This invite is not for you")
    if invite.status != "pending":
        raise HTTPException(status_code=400, detail=f"Invite already {invite.status}")

    if invite.target_type == "room":
        room = await session.get(ChatRoom, invite.target_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room no longer exists")
        # Add as room member
        existing = await session.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room.id,
                ChatRoomMember.user_id == user.id,
            )
        )
        if not existing.scalar_one_or_none():
            session.add(
                ChatRoomMember(
                    room_id=room.id,
                    user_id=user.id,
                    added_by=invite.invited_by,
                )
            )

    elif invite.target_type == "community":
        community = await session.get(Community, invite.target_id)
        if not community:
            raise HTTPException(status_code=404, detail="Community no longer exists")
        # Add as community member
        existing = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == community.id,
                CommunityMembership.user_id == user.id,
            )
        )
        if not existing.scalar_one_or_none():
            session.add(
                CommunityMembership(
                    community_id=community.id,
                    user_id=user.id,
                    role="member",
                )
            )

    invite.status = "accepted"
    invite.responded_at = datetime.now(UTC)
    session.add(invite)
    await session.flush()

    return _invite_response(invite)


@router.post("/{invite_id}/decline", response_model=InviteResponse)
async def decline_invite(
    invite_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    invite = await session.get(Invite, invite_id)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.invited_user_id != user.id:
        raise HTTPException(status_code=403, detail="This invite is not for you")
    if invite.status != "pending":
        raise HTTPException(status_code=400, detail=f"Invite already {invite.status}")

    invite.status = "declined"
    invite.responded_at = datetime.now(UTC)
    session.add(invite)
    await session.flush()

    return _invite_response(invite)
