from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, OptionalUser
from app.db.session import get_session
from app.models import ChatRoom, Community, CommunityMembership, CommunityRequest, User

from .schemas import (
    CommunityCreateRequest,
    CommunityRequestCreate,
    CommunityResponse,
    CommunityUpdateRequest,
    MemberResponse,
)

router = APIRouter(prefix="/api/communities", tags=["communities"])


def _to_response(c: Community, member_count: int = 0) -> CommunityResponse:
    return CommunityResponse(
        id=str(c.id),
        slug=c.slug,
        name=c.name,
        description=c.description,
        color=c.color,
        owner_id=str(c.owner_id),
        member_count=member_count,
        is_private=c.is_private,
        created_at=c.created_at,
    )


@router.get("", response_model=list[CommunityResponse])
async def list_communities(session: AsyncSession = Depends(get_session)):
    stmt = (
        select(Community, func.count(CommunityMembership.id).label("cnt"))
        .outerjoin(
            CommunityMembership,
            Community.id == CommunityMembership.community_id,
        )
        .where(Community.is_private.is_(False))
        .group_by(Community.id)
        .order_by(Community.name)
    )
    result = await session.execute(stmt)
    return [_to_response(row.Community, row.cnt) for row in result.all()]


@router.get("/mine", response_model=list[CommunityResponse])
async def my_communities(
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Community, func.count(CommunityMembership.id).label("cnt"))
        .join(
            CommunityMembership,
            Community.id == CommunityMembership.community_id,
        )
        .where(
            CommunityMembership.user_id == user.id,
            CommunityMembership.banned_at.is_(None),
        )
        .group_by(Community.id)
        .order_by(Community.name)
    )
    result = await session.execute(stmt)
    return [_to_response(row.Community, row.cnt) for row in result.all()]


@router.get("/{slug}")
async def get_community(
    slug: str,
    user: OptionalUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    membership = None
    if user:
        m_result = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == community.id,
                CommunityMembership.user_id == user.id,
            )
        )
        membership = m_result.scalar_one_or_none()

    # Private communities return 404 to non-members (and banned members)
    if community.is_private and (not membership or membership.banned_at):
        raise HTTPException(status_code=404, detail="Community not found")

    count_result = await session.execute(
        select(func.count())
        .select_from(CommunityMembership)
        .where(CommunityMembership.community_id == community.id)
    )
    count = count_result.scalar_one()

    resp = _to_response(community, count)
    return {
        **resp.model_dump(),
        "is_member": bool(membership and not membership.banned_at),
        "membership_role": (membership.role if membership and not membership.banned_at else None),
        "is_banned": bool(membership and membership.banned_at),
    }


@router.post("", response_model=CommunityResponse, status_code=201)
async def create_community(
    body: CommunityCreateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create communities")
    existing = await session.execute(select(Community).where(Community.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already taken")
    community = Community(
        name=body.name,
        slug=body.slug,
        description=body.description,
        color=body.color,
        is_private=body.is_private,
        owner_id=user.id,
    )
    session.add(community)
    await session.flush()
    session.add(CommunityMembership(community_id=community.id, user_id=user.id, role="owner"))
    await session.flush()
    session.add(
        ChatRoom(
            community_id=community.id,
            name="general",
            slug="general",
            is_default=True,
            created_by=user.id,
        )
    )
    await session.flush()
    return _to_response(community, 1)


@router.post("/{slug}/join", status_code=200)
async def join_community(
    slug: str,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    if community.is_private:
        raise HTTPException(
            status_code=403, detail="This is a private community — join by invite only"
        )
    existing = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.user_id == user.id,
        )
    )
    membership = existing.scalar_one_or_none()
    if membership:
        if membership.banned_at:
            raise HTTPException(status_code=403, detail="You are banned from this community")
        return {"status": "already_member"}
    session.add(CommunityMembership(community_id=community.id, user_id=user.id, role="member"))
    return {"status": "joined"}


@router.post("/{slug}/leave", status_code=200)
async def leave_community(
    slug: str,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    if community.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Owner cannot leave their community")
    m_result = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.user_id == user.id,
        )
    )
    membership = m_result.scalar_one_or_none()
    if not membership:
        return {"status": "not_member"}
    await session.delete(membership)
    return {"status": "left"}


@router.patch("/{slug}", response_model=CommunityResponse)
async def update_community(
    slug: str,
    body: CommunityUpdateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    if community.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the owner or admin can update")
    if body.name is not None:
        community.name = body.name
    if body.description is not None:
        community.description = body.description
    if body.color is not None:
        community.color = body.color
    session.add(community)
    await session.flush()
    count_result = await session.execute(
        select(func.count())
        .select_from(CommunityMembership)
        .where(CommunityMembership.community_id == community.id)
    )
    return _to_response(community, count_result.scalar_one())


@router.get("/{slug}/members", response_model=list[MemberResponse])
async def list_members(
    slug: str,
    user: OptionalUser,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    if community.is_private:
        membership = None
        if user:
            m_result = await session.execute(
                select(CommunityMembership).where(
                    CommunityMembership.community_id == community.id,
                    CommunityMembership.user_id == user.id,
                )
            )
            membership = m_result.scalar_one_or_none()
        if not membership or membership.banned_at:
            raise HTTPException(status_code=404, detail="Community not found")

    stmt = (
        select(CommunityMembership, User)
        .join(User, CommunityMembership.user_id == User.id)
        .where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.banned_at.is_(None),
        )
        .order_by(CommunityMembership.joined_at)
    )
    rows = await session.execute(stmt)
    return [
        MemberResponse(
            user_id=str(row.User.id),
            handle=row.User.handle,
            display_name=row.User.display_name,
            avatar_url=row.User.avatar_url,
            role=row.CommunityMembership.role,
            joined_at=row.CommunityMembership.joined_at,
        )
        for row in rows.all()
    ]


@router.post("/requests", status_code=201)
async def request_community(
    body: CommunityRequestCreate,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    session.add(
        CommunityRequest(
            requested_by=user.id,
            name=body.name,
            slug=body.slug,
            description=body.description,
        )
    )
    return {"status": "submitted"}
