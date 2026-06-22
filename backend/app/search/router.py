from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import Community, CommunityMembership, Post, QuestionTag, Tag, User

from .schemas import (
    SearchCommunityResult,
    SearchPostResult,
    SearchResponse,
    SearchTagResult,
    SearchUserResult,
)

router = APIRouter(tags=["search"])

LIMIT = 10


@router.get("/api/search", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=1, max_length=200),
    session: AsyncSession = Depends(get_session),
):
    pattern = f"%{q}%"

    tag_match_subq = (
        select(QuestionTag.question_id)
        .join(Tag, QuestionTag.tag_id == Tag.id)
        .where(Tag.name.ilike(pattern) | Tag.slug.ilike(pattern))
    )

    post_stmt = (
        select(Post, User, Community)
        .outerjoin(User, Post.author_id == User.id)
        .join(Community, Post.community_id == Community.id)
        .where(
            Post.deleted_at.is_(None),
            Post.removed_at.is_(None),
            or_(
                Post.title.ilike(pattern),
                Post.id.in_(tag_match_subq),
            ),
        )
        .order_by(Post.score.desc(), Post.created_at.desc())
        .limit(LIMIT)
    )
    post_rows = (await session.execute(post_stmt)).all()

    posts = [
        SearchPostResult(
            id=str(row.Post.id),
            title=row.Post.title,
            community_slug=row.Community.slug if row.Community else None,
            community_name=row.Community.name if row.Community else None,
            author_handle=row.User.handle if row.User else None,
            score=row.Post.score,
            comment_count=row.Post.comment_count,
            created_at=row.Post.created_at,
        )
        for row in post_rows
    ]

    comm_stmt = (
        select(Community, func.count(CommunityMembership.id).label("cnt"))
        .outerjoin(
            CommunityMembership,
            Community.id == CommunityMembership.community_id,
        )
        .where(
            Community.name.ilike(pattern) | Community.slug.ilike(pattern),
        )
        .group_by(Community.id)
        .order_by(Community.name)
        .limit(LIMIT)
    )
    comm_rows = (await session.execute(comm_stmt)).all()

    communities = [
        SearchCommunityResult(
            id=str(row.Community.id),
            slug=row.Community.slug,
            name=row.Community.name,
            description=row.Community.description,
            color=row.Community.color,
            member_count=row.cnt,
        )
        for row in comm_rows
    ]

    user_stmt = (
        select(User)
        .where(
            User.suspended_at.is_(None),
            User.handle.ilike(pattern) | User.display_name.ilike(pattern),
        )
        .order_by(User.handle)
        .limit(LIMIT)
    )
    user_rows = (await session.execute(user_stmt)).all()

    users = [
        SearchUserResult(
            id=str(row.User.id),
            handle=row.User.handle,
            display_name=row.User.display_name,
            avatar_url=row.User.avatar_url,
        )
        for row in user_rows
    ]

    tag_stmt = (
        select(Tag, Community.slug.label("comm_slug"))
        .join(Community, Tag.community_id == Community.id)
        .where(
            Tag.name.ilike(pattern) | Tag.slug.ilike(pattern),
        )
        .order_by(Tag.usage_count.desc())
        .limit(5)
    )
    tag_rows = (await session.execute(tag_stmt)).all()

    tags = [
        SearchTagResult(
            id=str(row.Tag.id),
            slug=row.Tag.slug,
            name=row.Tag.name,
            color=row.Tag.color,
            community_slug=row.comm_slug,
            usage_count=row.Tag.usage_count,
        )
        for row in tag_rows
    ]

    return SearchResponse(posts=posts, communities=communities, users=users, tags=tags)
