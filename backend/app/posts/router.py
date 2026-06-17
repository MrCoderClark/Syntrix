from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, OptionalUser
from app.db.session import get_session
from app.models import Community, CommunityMembership, Post, PostAttachment, User
from app.posts.renderer import render_tiptap_json

from .schemas import (
    CreatePostRequest,
    PostListResponse,
    PostResponse,
    RemovePostRequest,
    UpdatePostRequest,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])

PAGE_SIZE = 20


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
        body_json=post.body_json if not post.removed_at else None,
        body_html=post.body_html if not post.removed_at else "",
        score=post.score,
        comment_count=post.comment_count,
        is_pinned=post.is_pinned,
        deleted_at=post.deleted_at,
        removed_at=post.removed_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


async def _get_membership(
    session: AsyncSession,
    community_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CommunityMembership | None:
    result = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


def _extract_image_urls(body_json: dict) -> list[str]:
    urls: list[str] = []

    def _walk(node: dict) -> None:
        if node.get("type") == "image":
            src = node.get("attrs", {}).get("src")
            if src:
                urls.append(src)
        for child in node.get("content", []):
            _walk(child)

    _walk(body_json)
    return urls


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    body: CreatePostRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    community = await session.get(Community, body.community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    membership = await _get_membership(session, community.id, user.id)
    if not membership or membership.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to post")

    body_html = render_tiptap_json(body.body_json)

    post = Post(
        community_id=community.id,
        author_id=user.id,
        title=body.title,
        body_json=body.body_json,
        body_html=body_html,
    )
    session.add(post)
    await session.flush()
    await session.refresh(post)

    image_urls = _extract_image_urls(body.body_json)
    for url in image_urls:
        parts = url.split("/storage/v1/object/public/syntrix-uploads/")
        key = parts[-1] if len(parts) > 1 else url
        session.add(
            PostAttachment(
                post_id=post.id,
                storage_key=key,
                content_type="image/jpeg",
            )
        )

    return _post_response(post, author=user, community=community)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    user: OptionalUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    author = await session.get(User, post.author_id) if post.author_id else None
    community = await session.get(Community, post.community_id)

    return _post_response(post, author=author, community=community)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    body: UpdatePostRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.removed_at:
        raise HTTPException(status_code=403, detail="Cannot edit a removed post")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the author can edit")

    if body.title is not None:
        post.title = body.title
    if body.body_json is not None:
        post.body_json = body.body_json
        post.body_html = render_tiptap_json(body.body_json)

    await session.flush()
    await session.refresh(post)

    community = await session.get(Community, post.community_id)
    return _post_response(post, author=user, community=community)


@router.delete("/{post_id}", status_code=200)
async def delete_post(
    post_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the author can delete")

    post.deleted_at = datetime.now(UTC)
    session.add(post)
    return {"status": "deleted"}


@router.post("/{post_id}/remove", response_model=PostResponse)
async def remove_post(
    post_id: uuid.UUID,
    body: RemovePostRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    if user.role != "admin":
        membership = await _get_membership(session, post.community_id, user.id)
        if not membership or membership.role not in ("mod", "owner"):
            raise HTTPException(status_code=403, detail="Only mods, owners, or admins can remove")

    post.removed_at = datetime.now(UTC)
    post.removed_by = user.id
    post.removed_reason = body.reason
    await session.flush()
    await session.refresh(post)

    author = await session.get(User, post.author_id) if post.author_id else None
    community = await session.get(Community, post.community_id)
    return _post_response(post, author=author, community=community)


@router.post("/{post_id}/pin", status_code=200)
async def pin_post(
    post_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    if user.role != "admin":
        membership = await _get_membership(session, post.community_id, user.id)
        if not membership or membership.role not in ("mod", "owner"):
            raise HTTPException(status_code=403, detail="Only mods, owners, or admins can pin")

    await session.execute(
        update(Post)
        .where(Post.community_id == post.community_id, Post.is_pinned.is_(True))
        .values(is_pinned=False)
    )

    post.is_pinned = True
    session.add(post)
    return {"status": "pinned"}


@router.post("/{post_id}/unpin", status_code=200)
async def unpin_post(
    post_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    if user.role != "admin":
        membership = await _get_membership(session, post.community_id, user.id)
        if not membership or membership.role not in ("mod", "owner"):
            raise HTTPException(status_code=403, detail="Only mods, owners, or admins can unpin")

    post.is_pinned = False
    session.add(post)
    return {"status": "unpinned"}


@router.get("/community/{community_id}", response_model=PostListResponse)
async def list_community_posts(
    community_id: uuid.UUID,
    cursor: str | None = None,
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
        .order_by(Post.is_pinned.desc(), Post.created_at.desc())
        .limit(PAGE_SIZE + 1)
    )

    if cursor:
        from datetime import datetime as dt

        cursor_time = dt.fromisoformat(cursor)
        stmt = stmt.where(Post.created_at < cursor_time)

    result = await session.execute(stmt)
    rows = result.all()

    posts = []
    for row in rows[:PAGE_SIZE]:
        post = row.Post
        author = row.User
        posts.append(_post_response(post, author=author, community=community))

    next_cursor = None
    if len(rows) > PAGE_SIZE:
        next_cursor = posts[-1].created_at.isoformat()

    return PostListResponse(posts=posts, next_cursor=next_cursor)
