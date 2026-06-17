from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.comments.tree import build_comment_tree, compute_path, depth_from_path
from app.db.session import get_session
from app.models import Comment, CommunityMembership, Post, User
from app.posts.renderer import render_tiptap_json

from .schemas import (
    CommentListResponse,
    CommentResponse,
    CreateCommentRequest,
    RemoveCommentRequest,
)

router = APIRouter(tags=["comments"])


def _comment_response(comment: Comment, author: User | None = None) -> dict:
    body = comment.body_html
    if comment.deleted_at:
        body = "[deleted]"
    elif comment.removed_at:
        body = "[removed by moderator]"

    return {
        "id": str(comment.id),
        "post_id": str(comment.post_id),
        "author_id": str(comment.author_id) if comment.author_id else None,
        "author_handle": author.handle if author and not comment.deleted_at else None,
        "author_display_name": (author.display_name if author and not comment.deleted_at else None),
        "author_avatar_url": (author.avatar_url if author and not comment.deleted_at else None),
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "depth": comment.depth,
        "path": comment.path,
        "body_html": body,
        "score": comment.score,
        "deleted_at": comment.deleted_at,
        "removed_at": comment.removed_at,
        "created_at": comment.created_at,
    }


@router.post(
    "/api/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
async def create_comment(
    post_id: uuid.UUID,
    body: CreateCommentRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    membership = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == post.community_id,
            CommunityMembership.user_id == user.id,
        )
    )
    mem = membership.scalar_one_or_none()
    if not mem or mem.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to comment")

    parent_path = None
    parent_id = None
    if body.parent_comment_id:
        parent = await session.get(Comment, body.parent_comment_id)
        if not parent or parent.post_id != post_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        parent_path = parent.path
        parent_id = parent.id

    comment_id = uuid.uuid4()
    id_hex = comment_id.hex[:8]

    try:
        path = compute_path(parent_path, id_hex)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    depth = depth_from_path(path)
    body_html = render_tiptap_json(body.body_json)

    comment = Comment(
        id=comment_id,
        post_id=post_id,
        author_id=user.id,
        parent_id=parent_id,
        path=path,
        depth=depth,
        body_json=body.body_json,
        body_html=body_html,
    )
    session.add(comment)
    await session.flush()
    await session.refresh(comment)

    resp = _comment_response(comment, author=user)
    resp.pop("path")
    return resp


@router.get(
    "/api/posts/{post_id}/comments",
    response_model=CommentListResponse,
)
async def list_comments(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    result = await session.execute(
        select(Comment, User)
        .outerjoin(User, Comment.author_id == User.id)
        .where(Comment.post_id == post_id)
        .order_by(text("path"))
    )
    rows = result.all()

    flat = []
    for row in rows:
        comment = row.Comment
        author = row.User
        data = _comment_response(comment, author=author)
        flat.append(data)

    tree = build_comment_tree(flat)

    def _strip_path(nodes: list[dict]) -> list[dict]:
        for n in nodes:
            n.pop("path", None)
            _strip_path(n.get("children", []))
        return nodes

    _strip_path(tree)

    return CommentListResponse(comments=tree, total_count=len(flat))


@router.delete("/api/comments/{comment_id}", status_code=200)
async def delete_comment(
    comment_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(Comment, comment_id)
    if not comment or comment.deleted_at:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the author can delete")

    comment.deleted_at = datetime.now(UTC)
    return {"status": "deleted"}


@router.post("/api/comments/{comment_id}/remove", response_model=CommentResponse)
async def remove_comment(
    comment_id: uuid.UUID,
    body: RemoveCommentRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(Comment, comment_id)
    if not comment or comment.deleted_at:
        raise HTTPException(status_code=404, detail="Comment not found")

    post = await session.get(Post, comment.post_id)
    if user.role != "admin":
        membership = await session.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == post.community_id,
                CommunityMembership.user_id == user.id,
            )
        )
        mem = membership.scalar_one_or_none()
        if not mem or mem.role not in ("mod", "owner"):
            raise HTTPException(
                status_code=403,
                detail="Only mods, owners, or admins can remove",
            )

    comment.removed_at = datetime.now(UTC)
    comment.removed_by = user.id
    comment.removed_reason = body.reason
    await session.flush()
    await session.refresh(comment)

    author = await session.get(User, comment.author_id) if comment.author_id else None
    resp = _comment_response(comment, author=author)
    resp.pop("path", None)
    return resp
