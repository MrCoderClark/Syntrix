from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, OptionalUser
from app.db.session import get_session
from app.models import AnswerVote, Comment, CommentVote, CommunityMembership, Post, PostVote
from app.reputation.engine import award_rep

from .schemas import BatchVotesResponse, VoteRequest, VoteResponse, VoteTargetType

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
    if post.removed_at:
        raise HTTPException(status_code=403, detail="Cannot vote on a removed post")

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

    old_vote_q = select(PostVote.value).where(
        PostVote.user_id == user.id,
        PostVote.post_id == post_id,
    )
    old_result = await session.execute(old_vote_q)
    old_val = old_result.scalar_one_or_none()

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

    if post.post_type == "question" and post.author_id:
        if old_val == 1:
            await award_rep(
                session,
                post.author_id,
                "question_upvoted",
                post.id,
                reverse=True,
            )
        elif old_val == -1:
            await award_rep(
                session,
                post.author_id,
                "question_downvoted",
                post.id,
                reverse=True,
            )
        if body.value == 1:
            await award_rep(
                session,
                post.author_id,
                "question_upvoted",
                post.id,
            )
        elif body.value == -1:
            await award_rep(
                session,
                post.author_id,
                "question_downvoted",
                post.id,
            )

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
    if comment.removed_at:
        raise HTTPException(status_code=403, detail="Cannot vote on a removed comment")

    if comment.author_id == user.id:
        raise HTTPException(status_code=403, detail="Cannot vote on your own comment")

    post = await session.get(Post, comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
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


@router.get("/api/votes/mine", response_model=BatchVotesResponse)
async def batch_my_votes(
    target_type: VoteTargetType,
    target_ids: str = Query(max_length=2000),
    user: OptionalUser = None,
    session: AsyncSession = Depends(get_session),
):
    # Auth check after query param validation so invalid enum returns 422, not 401
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    raw_ids = [s.strip() for s in target_ids.split(",") if s.strip()]
    if len(raw_ids) > 50:
        raise HTTPException(status_code=422, detail="Max 50 IDs per request")

    try:
        parsed = [uuid.UUID(i) for i in raw_ids]
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID in target_ids") from None

    model_map = {
        VoteTargetType.post: (PostVote, PostVote.post_id),
        VoteTargetType.comment: (CommentVote, CommentVote.comment_id),
        VoteTargetType.answer: (AnswerVote, AnswerVote.answer_id),
    }
    vote_model, id_col = model_map[target_type]

    stmt = select(id_col, vote_model.value).where(
        vote_model.user_id == user.id,
        id_col.in_(parsed),
    )
    result = await session.execute(stmt)
    votes = {str(row[0]): row[1] for row in result.all()}

    return BatchVotesResponse(votes=votes)
