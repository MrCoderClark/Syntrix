from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.auth.rate_limit import check_rate_limit
from app.db.session import get_session
from app.models import ChatMessage, ChatRoom, ChatRoomMember, Community, CommunityMembership, User
from app.posts.renderer import render_tiptap_json
from app.redis import publish_event

from .schemas import (
    AddRoomMemberRequest,
    CreateRoomRequest,
    EditMessageRequest,
    MessageResponse,
    RoomMemberResponse,
    RoomResponse,
    SendMessageRequest,
)

router = APIRouter(tags=["chat"])

MESSAGE_PAGE_SIZE = 50


async def _require_membership(
    session: AsyncSession,
    community_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CommunityMembership:
    result = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.banned_at:
        raise HTTPException(status_code=403, detail="Not a member of this community")
    return membership


async def _require_room_access(
    session: AsyncSession,
    room: ChatRoom,
    user_id: uuid.UUID,
) -> None:
    """Check room access.

    For private rooms/DMs, verify chat_room_members.
    For public rooms, verify community membership.
    """
    if room.is_private or room.is_dm:
        result = await session.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room.id,
                ChatRoomMember.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this room")
    elif room.community_id:
        await _require_membership(session, room.community_id, user_id)
    else:
        raise HTTPException(status_code=403, detail="Cannot access this room")


def _room_response(room: ChatRoom) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        community_id=room.community_id,
        name=room.name,
        slug=room.slug,
        description=room.description,
        is_default=room.is_default,
        is_private=room.is_private,
        is_dm=room.is_dm,
        created_by=room.created_by,
        created_at=room.created_at,
    )


def _message_response(
    msg: ChatMessage,
    *,
    author: User | None = None,
) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        room_id=msg.room_id,
        author_id=msg.author_id,
        author_handle=author.handle if author else None,
        author_display_name=author.display_name if author else None,
        author_avatar_url=author.avatar_url if author else None,
        body_json=msg.body_json if not msg.deleted_at else None,
        body_html=msg.body_html if not msg.deleted_at else "",
        edited_at=msg.edited_at,
        deleted_at=msg.deleted_at,
        created_at=msg.created_at,
    )


# ---------------------------------------------------------------------------
# Room endpoints
# ---------------------------------------------------------------------------


@router.get("/api/communities/{community_id}/rooms", response_model=list[RoomResponse])
async def list_rooms(
    community_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    await _require_membership(session, community_id, user.id)
    result = await session.execute(
        select(ChatRoom)
        .where(
            ChatRoom.community_id == community_id,
            ChatRoom.is_dm.is_(False),
        )
        .where(
            (ChatRoom.is_private.is_(False))
            | ChatRoom.id.in_(
                select(ChatRoomMember.room_id).where(ChatRoomMember.user_id == user.id)
            )
        )
        .order_by(ChatRoom.is_default.desc(), ChatRoom.name)
    )
    return [_room_response(r) for r in result.scalars().all()]


@router.post("/api/communities/{community_id}/rooms", response_model=RoomResponse, status_code=201)
async def create_room(
    community_id: uuid.UUID,
    body: CreateRoomRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    membership = await _require_membership(session, community_id, user.id)
    if membership.role not in ("mod", "owner") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only mods, owners, or admins can create rooms")

    community = await session.get(Community, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    existing = await session.execute(
        select(ChatRoom).where(
            ChatRoom.community_id == community_id,
            ChatRoom.slug == body.slug,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Room slug already taken in this community")

    room = ChatRoom(
        community_id=community_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        is_private=body.is_private,
        created_by=user.id,
    )
    session.add(room)
    await session.flush()

    if room.is_private:
        session.add(ChatRoomMember(room_id=room.id, user_id=user.id, added_by=user.id))
        await session.flush()

    return _room_response(room)


@router.get("/api/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)
    return _room_response(room)


@router.delete("/api/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete the default room")
    membership = await _require_membership(session, room.community_id, user.id)
    if membership.role not in ("mod", "owner") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only mods, owners, or admins can delete rooms")
    await session.delete(room)
    await session.flush()


# ---------------------------------------------------------------------------
# Message endpoints
# ---------------------------------------------------------------------------


@router.post("/api/rooms/{room_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    room_id: uuid.UUID,
    body: SendMessageRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)

    conn = await session.connection()
    allowed = await check_rate_limit(
        conn,
        key=f"chat:send:{user.id}",
        max_tokens=120,
        refill_rate=120 / 3600,
        cost=1,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Message rate limit exceeded")

    body_html = render_tiptap_json(body.body_json)

    msg = ChatMessage(
        room_id=room_id,
        author_id=user.id,
        body_json=body.body_json,
        body_html=body_html,
    )
    session.add(msg)
    await session.flush()

    resp = _message_response(msg, author=user)
    await publish_event(
        f"syntrix:room:{room_id}",
        "message.created",
        resp.model_dump(mode="json"),
        room_id=str(room_id),
    )
    return resp


@router.get("/api/rooms/{room_id}/messages", response_model=list[MessageResponse])
async def message_history(
    room_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    before: str | None = None,
    limit: int = MESSAGE_PAGE_SIZE,
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)

    limit = max(1, min(limit, MESSAGE_PAGE_SIZE))
    stmt = (
        select(ChatMessage, User)
        .outerjoin(User, ChatMessage.author_id == User.id)
        .where(ChatMessage.room_id == room_id)
    )
    if before:
        try:
            cursor_id = uuid.UUID(before)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor") from None
        cursor_msg = await session.get(ChatMessage, cursor_id)
        if not cursor_msg:
            return []
        stmt = stmt.where(
            (ChatMessage.created_at < cursor_msg.created_at)
            | ((ChatMessage.created_at == cursor_msg.created_at) & (ChatMessage.id < cursor_id))
        )
    stmt = stmt.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit)
    result = await session.execute(stmt)
    return [_message_response(row.ChatMessage, author=row.User) for row in result.all()]


@router.patch("/api/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: uuid.UUID,
    body: EditMessageRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    msg = await session.get(ChatMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.author_id != user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own messages")
    if msg.deleted_at:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted message")

    room = await session.get(ChatRoom, msg.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)

    msg.body_json = body.body_json
    msg.body_html = render_tiptap_json(body.body_json)
    msg.edited_at = datetime.now(UTC)
    session.add(msg)
    await session.flush()

    author = await session.get(User, msg.author_id)
    resp = _message_response(msg, author=author)
    await publish_event(
        f"syntrix:room:{msg.room_id}",
        "message.edited",
        resp.model_dump(mode="json"),
        room_id=str(msg.room_id),
    )
    return resp


@router.delete("/api/messages/{message_id}", status_code=200)
async def delete_message(
    message_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    msg = await session.get(ChatMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    room = await session.get(ChatRoom, msg.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)

    is_author = msg.author_id == user.id
    is_mod = user.role == "admin"
    if room.community_id and not is_author:
        community_membership = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == room.community_id,
                CommunityMembership.user_id == user.id,
            )
        )
        cm = community_membership.scalar_one_or_none()
        if cm and cm.role in ("mod", "owner"):
            is_mod = True
    if not is_author and not is_mod:
        raise HTTPException(status_code=403, detail="Cannot delete this message")

    msg.deleted_at = datetime.now(UTC)
    session.add(msg)
    await session.flush()

    await publish_event(
        f"syntrix:room:{msg.room_id}",
        "message.deleted",
        {"id": str(msg.id), "room_id": str(msg.room_id)},
        room_id=str(msg.room_id),
    )
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Room member management endpoints
# ---------------------------------------------------------------------------


@router.get("/api/rooms/{room_id}/members", response_model=list[RoomMemberResponse])
async def list_room_members(
    room_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await _require_room_access(session, room, user.id)

    result = await session.execute(
        select(ChatRoomMember, User)
        .join(User, ChatRoomMember.user_id == User.id)
        .where(ChatRoomMember.room_id == room_id)
        .order_by(ChatRoomMember.created_at)
    )
    return [
        RoomMemberResponse(
            user_id=row.User.id,
            handle=row.User.handle,
            display_name=row.User.display_name,
            avatar_url=row.User.avatar_url,
            added_by=row.ChatRoomMember.added_by,
            created_at=row.ChatRoomMember.created_at,
        )
        for row in result.all()
    ]


@router.post("/api/rooms/{room_id}/members", status_code=201)
async def add_room_member(
    room_id: uuid.UUID,
    body: AddRoomMemberRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room.is_private and not room.is_dm:
        raise HTTPException(status_code=400, detail="Can only add members to private rooms")

    # Must be a room member or community mod/owner/admin to add members
    is_privileged = user.role == "admin"
    if room.community_id:
        community_membership_result = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == room.community_id,
                CommunityMembership.user_id == user.id,
            )
        )
        cm = community_membership_result.scalar_one_or_none()
        if cm and cm.role in ("mod", "owner"):
            is_privileged = True

    # Room members can also add to rooms they belong to
    own_rm = await session.execute(
        select(ChatRoomMember).where(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user.id,
        )
    )
    if not own_rm.scalar_one_or_none() and not is_privileged:
        raise HTTPException(status_code=403, detail="Not authorized to add members")

    # Check target user exists
    target = await session.get(User, body.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a member
    existing = await session.execute(
        select(ChatRoomMember).where(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_member"}

    session.add(ChatRoomMember(room_id=room_id, user_id=body.user_id, added_by=user.id))
    await session.flush()
    return {"status": "added"}


@router.delete("/api/rooms/{room_id}/members/{target_user_id}", status_code=200)
async def remove_room_member(
    room_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Can remove self, or mod/owner/admin can remove others
    is_self = target_user_id == user.id
    is_privileged = user.role == "admin"
    if room.community_id and not is_self:
        community_membership_result = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == room.community_id,
                CommunityMembership.user_id == user.id,
            )
        )
        cm = community_membership_result.scalar_one_or_none()
        if cm and cm.role in ("mod", "owner"):
            is_privileged = True

    # For private rooms, requester must also be a room member (unless they're admin)
    if (room.is_private or room.is_dm) and not is_self and not is_privileged:
        own_rm = await session.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room_id,
                ChatRoomMember.user_id == user.id,
            )
        )
        if not own_rm.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this room")

    if not is_self and not is_privileged:
        raise HTTPException(status_code=403, detail="Not authorized to remove members")

    result = await session.execute(
        select(ChatRoomMember).where(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == target_user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return {"status": "not_member"}

    await session.delete(member)
    await session.flush()
    return {"status": "removed"}
