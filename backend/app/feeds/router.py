from __future__ import annotations

import uuid
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import OptionalUser
from app.db.session import get_session
from app.models import Community, CommunityMembership, Post, User
from app.posts.schemas import PostListResponse, PostResponse

from .algorithms import hot_order, new_order, top_order, top_period_filter

router = APIRouter(tags=["feeds"])

PAGE_SIZE = 25


class SortMode(str, Enum):
    hot = "hot"
    new = "new"
    top = "top"


def _post_response(
    post: Post,
    *,
    author: User | None = None,
    community: Community | None = None,
) -> PostResponse:
    return PostResponse(
        id=post.id,
        community_id=post.community_id,
        community_slug=community.slug if community else None,
        community_name=community.name if community else None,
        author_id=post.author_id,
        author_handle=author.handle if author else None,
        author_display_name=author.display_name if author else None,
        author_avatar_url=author.avatar_url if author else None,
        title=post.title,
        body_html=post.body_html if not post.removed_at else "",
        score=post.score,
        comment_count=post.comment_count,
        is_pinned=post.is_pinned,
        deleted_at=post.deleted_at,
        removed_at=post.removed_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _apply_sort(stmt, sort: SortMode, period: str | None):
    if sort == SortMode.hot:
        return stmt.order_by(*hot_order())
    elif sort == SortMode.new:
        return stmt.order_by(*new_order())
    elif sort == SortMode.top:
        period_filter = top_period_filter(period or "all")
        if period_filter is not None:
            stmt = stmt.where(period_filter)
        return stmt.order_by(*top_order())
    return stmt


@router.get("/api/feed", response_model=PostListResponse)
async def home_feed(
    sort: SortMode = SortMode.hot,
    period: str | None = None,
    limit: int = Query(default=PAGE_SIZE, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    user: OptionalUser = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Post, User, Community)
        .outerjoin(User, Post.author_id == User.id)
        .join(Community, Post.community_id == Community.id)
        .where(Post.deleted_at.is_(None))
    )

    if user:
        stmt = stmt.join(
            CommunityMembership,
            (CommunityMembership.community_id == Post.community_id)
            & (CommunityMembership.user_id == user.id)
            & (CommunityMembership.banned_at.is_(None)),
        )

    stmt = _apply_sort(stmt, sort, period)
    stmt = stmt.offset(offset).limit(limit + 1)

    result = await session.execute(stmt)
    rows = result.all()

    posts = []
    for row in rows[:limit]:
        posts.append(_post_response(row.Post, author=row.User, community=row.Community))

    next_cursor = None
    if len(rows) > limit:
        next_cursor = str(offset + limit)

    return PostListResponse(posts=posts, next_cursor=next_cursor)


@router.get("/api/communities/{community_id}/feed", response_model=PostListResponse)
async def community_feed(
    community_id: uuid.UUID,
    sort: SortMode = SortMode.hot,
    period: str | None = None,
    limit: int = Query(default=PAGE_SIZE, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    community = await session.get(Community, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    stmt = (
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(
            Post.community_id == community_id,
            Post.deleted_at.is_(None),
        )
    )

    if sort == SortMode.top:
        period_filter = top_period_filter(period or "all")
        if period_filter is not None:
            stmt = stmt.where(period_filter)

    sort_orders = {
        SortMode.hot: hot_order,
        SortMode.new: new_order,
        SortMode.top: top_order,
    }
    stmt = stmt.order_by(Post.is_pinned.desc(), *sort_orders[sort]())

    stmt = stmt.offset(offset).limit(limit + 1)

    result = await session.execute(stmt)
    rows = result.all()

    posts = []
    for row in rows[:limit]:
        posts.append(_post_response(row.Post, author=row.User, community=community))

    next_cursor = None
    if len(rows) > limit:
        next_cursor = str(offset + limit)

    return PostListResponse(posts=posts, next_cursor=next_cursor)
