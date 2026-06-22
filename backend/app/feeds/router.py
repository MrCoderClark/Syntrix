from __future__ import annotations

import uuid
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import OptionalUser
from app.db.session import get_session
from app.models import Community, CommunityMembership, Post, QuestionTag, Tag, User
from app.posts.schemas import PostListResponse, PostResponse, PostTagResponse

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
    tags: list[PostTagResponse] | None = None,
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
        post_type=post.post_type,
        answer_count=post.answer_count,
        has_accepted_answer=post.has_accepted_answer,
        tags=tags or [],
        deleted_at=post.deleted_at,
        removed_at=post.removed_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


async def _load_tags_for_posts(
    session: AsyncSession,
    posts: list[Post],
) -> dict[uuid.UUID, list[PostTagResponse]]:
    question_ids = [p.id for p in posts if p.post_type == "question"]
    if not question_ids:
        return {}
    stmt = (
        select(QuestionTag.question_id, Tag.id, Tag.slug, Tag.name, Tag.color)
        .join(Tag, QuestionTag.tag_id == Tag.id)
        .where(QuestionTag.question_id.in_(question_ids))
    )
    result = await session.execute(stmt)
    tags_by_post: dict[uuid.UUID, list[PostTagResponse]] = {}
    for row in result.all():
        qid = row[0]
        tag = PostTagResponse(id=str(row[1]), slug=row[2], name=row[3], color=row[4])
        tags_by_post.setdefault(qid, []).append(tag)
    return tags_by_post


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
    post_type: str | None = None,
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

    if post_type in ("discussion", "question"):
        stmt = stmt.where(Post.post_type == post_type)

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

    post_objs = [row.Post for row in rows[:limit]]
    tags_map = await _load_tags_for_posts(session, post_objs)

    posts = []
    for row in rows[:limit]:
        posts.append(
            _post_response(
                row.Post,
                author=row.User,
                community=row.Community,
                tags=tags_map.get(row.Post.id),
            )
        )

    next_cursor = None
    if len(rows) > limit:
        next_cursor = str(offset + limit)

    return PostListResponse(posts=posts, next_cursor=next_cursor)


@router.get("/api/communities/{community_id}/feed", response_model=PostListResponse)
async def community_feed(
    community_id: uuid.UUID,
    sort: SortMode = SortMode.hot,
    period: str | None = None,
    post_type: str | None = None,
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

    if post_type in ("discussion", "question"):
        stmt = stmt.where(Post.post_type == post_type)

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

    post_objs = [row.Post for row in rows[:limit]]
    tags_map = await _load_tags_for_posts(session, post_objs)

    posts = []
    for row in rows[:limit]:
        posts.append(
            _post_response(
                row.Post,
                author=row.User,
                community=community,
                tags=tags_map.get(row.Post.id),
            )
        )

    next_cursor = None
    if len(rows) > limit:
        next_cursor = str(offset + limit)

    return PostListResponse(posts=posts, next_cursor=next_cursor)
