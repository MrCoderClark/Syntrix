from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models import Comment, CommentVote, CommunityMembership, Post, PostVote

from .schemas import VoteRequest, VoteResponse

router = APIRouter(tags=["votes"])


@router.post("/api/posts/{post_id}/vote", response_model=VoteResponse)
async def vote_post(
    post_id: uuid.UUID,
    body: VoteRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id == user.id:
        raise HTTPException(status_code=403, detail="Cannot vote on your own post")

    membership = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == post.community_id,
            CommunityMembership.user_id == user.id,
        )
    )
    mem = membership.scalar_one_or_none()
    if not mem or mem.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to vote")

    if body.value == 0:
        await session.execute(
            delete(PostVote).where(
                PostVote.user_id == user.id,
                PostVote.post_id == post_id,
            )
        )
    else:
        stmt = pg_insert(PostVote).values(
            id=uuid.uuid4(),
            user_id=user.id,
            post_id=post_id,
            value=body.value,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_post_votes_user_post",
            set_={"value": body.value},
        )
        await session.execute(stmt)

    await session.flush()
    await session.refresh(post)

    return VoteResponse(score=post.score, user_vote=body.value)


@router.post("/api/comments/{comment_id}/vote", response_model=VoteResponse)
async def vote_comment(
    comment_id: uuid.UUID,
    body: VoteRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(Comment, comment_id)
    if not comment or comment.deleted_at:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id == user.id:
        raise HTTPException(status_code=403, detail="Cannot vote on your own comment")

    post = await session.get(Post, comment.post_id)
    membership = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == post.community_id,
            CommunityMembership.user_id == user.id,
        )
    )
    mem = membership.scalar_one_or_none()
    if not mem or mem.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to vote")

    if body.value == 0:
        await session.execute(
            delete(CommentVote).where(
                CommentVote.user_id == user.id,
                CommentVote.comment_id == comment_id,
            )
        )
    else:
        stmt = pg_insert(CommentVote).values(
            id=uuid.uuid4(),
            user_id=user.id,
            comment_id=comment_id,
            value=body.value,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_comment_votes_user_comment",
            set_={"value": body.value},
        )
        await session.execute(stmt)

    await session.flush()
    await session.refresh(comment)

    return VoteResponse(score=comment.score, user_vote=body.value)
