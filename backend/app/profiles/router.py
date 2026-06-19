from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models import User
from app.models.comment import Comment
from app.models.community import Community, CommunityMembership
from app.models.post import Post
from app.models.reputation import Badge, UserBadge
from app.profiles.schemas import (
    CommunityBrief,
    ProfileBadge,
    ProfileResponse,
    ProfileUpdateRequest,
    UserActivityResponse,
    UserCommentItem,
    UserPostItem,
)

router = APIRouter(prefix="/api/users", tags=["profiles"])


async def _build_profile(user: User, session: AsyncSession) -> ProfileResponse:
    post_count_q = (
        select(func.count())
        .select_from(Post)
        .where(Post.author_id == user.id, Post.deleted_at.is_(None), Post.removed_at.is_(None))
    )
    comment_count_q = (
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.author_id == user.id,
            Comment.deleted_at.is_(None),
            Comment.removed_at.is_(None),
        )
    )
    post_karma_q = select(func.coalesce(func.sum(Post.score), 0)).where(
        Post.author_id == user.id, Post.deleted_at.is_(None), Post.removed_at.is_(None)
    )
    comment_karma_q = select(func.coalesce(func.sum(Comment.score), 0)).where(
        Comment.author_id == user.id,
        Comment.deleted_at.is_(None),
        Comment.removed_at.is_(None),
    )
    communities_q = (
        select(Community.slug, Community.name, Community.color)
        .join(CommunityMembership, CommunityMembership.community_id == Community.id)
        .where(
            CommunityMembership.user_id == user.id,
            CommunityMembership.banned_at.is_(None),
        )
        .order_by(Community.name)
    )
    badges_q = (
        select(
            Badge.slug,
            Badge.name,
            Badge.icon,
            Badge.tier,
            UserBadge.awarded_at,
        )
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
        .order_by(UserBadge.awarded_at.desc())
    )

    pc, cc, pk, ck, comms, badges_rows = await asyncio.gather(
        _scalar(session, post_count_q),
        _scalar(session, comment_count_q),
        _scalar(session, post_karma_q),
        _scalar(session, comment_karma_q),
        session.execute(communities_q),
        session.execute(badges_q),
    )

    return ProfileResponse(
        id=str(user.id),
        handle=user.handle,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        audience_tag=user.audience_tag,
        role=user.role,
        github_username=user.github_username,
        discord_username=user.discord_username,
        website_url=user.website_url,
        post_count=pc,
        comment_count=cc,
        karma=pk + ck,
        reputation=user.reputation,
        badges=[
            ProfileBadge(
                slug=r.slug,
                name=r.name,
                icon=r.icon,
                tier=r.tier,
                awarded_at=r.awarded_at,
            )
            for r in badges_rows
        ],
        communities=[CommunityBrief(slug=r.slug, name=r.name, color=r.color) for r in comms],
        created_at=user.created_at,
    )


async def _scalar(session: AsyncSession, stmt):
    result = await session.execute(stmt)
    return result.scalar_one()


@router.get("/{handle}", response_model=ProfileResponse)
async def get_profile(handle: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.handle == handle))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await _build_profile(user, session)


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if body.handle is not None and body.handle != user.handle:
        existing = await session.execute(select(User).where(User.handle == body.handle))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Handle already taken")
        user.handle = body.handle

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.bio is not None:
        user.bio = body.bio
    if body.audience_tag is not None:
        user.audience_tag = body.audience_tag
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    if body.github_username is not None:
        user.github_username = body.github_username
    if body.discord_username is not None:
        user.discord_username = body.discord_username
    if body.website_url is not None:
        user.website_url = body.website_url if body.website_url != "" else None

    session.add(user)
    await session.flush()
    return await _build_profile(user, session)


@router.get("/{handle}/posts", response_model=UserActivityResponse)
async def get_user_posts(
    handle: str,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    user_row = await session.execute(select(User).where(User.handle == handle))
    user = user_row.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    base = (
        select(
            Post.id,
            Post.title,
            Post.score,
            Post.comment_count,
            Community.slug.label("community_slug"),
            Community.name.label("community_name"),
            Post.created_at,
        )
        .join(Community, Community.id == Post.community_id)
        .where(
            Post.author_id == user.id,
            Post.deleted_at.is_(None),
            Post.removed_at.is_(None),
        )
    )

    total_r = await session.execute(select(func.count()).select_from(base.subquery()))
    total = total_r.scalar_one()

    rows = await session.execute(base.order_by(Post.created_at.desc()).limit(limit).offset(offset))

    return UserActivityResponse(
        items=[
            UserPostItem(
                id=str(r.id),
                title=r.title,
                score=r.score,
                comment_count=r.comment_count,
                community_slug=r.community_slug,
                community_name=r.community_name,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
    )


@router.get("/{handle}/comments", response_model=UserActivityResponse)
async def get_user_comments(
    handle: str,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    user_row = await session.execute(select(User).where(User.handle == handle))
    user = user_row.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    base = (
        select(
            Comment.id,
            Comment.body_html,
            Comment.score,
            Post.id.label("post_id"),
            Post.title.label("post_title"),
            Community.slug.label("community_slug"),
            Comment.created_at,
        )
        .join(Post, Post.id == Comment.post_id)
        .join(Community, Community.id == Post.community_id)
        .where(
            Comment.author_id == user.id,
            Comment.deleted_at.is_(None),
            Comment.removed_at.is_(None),
        )
    )

    total_r = await session.execute(select(func.count()).select_from(base.subquery()))
    total = total_r.scalar_one()

    rows = await session.execute(
        base.order_by(Comment.created_at.desc()).limit(limit).offset(offset)
    )

    return UserActivityResponse(
        items=[
            UserCommentItem(
                id=str(r.id),
                body_html=r.body_html,
                score=r.score,
                post_id=str(r.post_id),
                post_title=r.post_title,
                community_slug=r.community_slug,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
    )
