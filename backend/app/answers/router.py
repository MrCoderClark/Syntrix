from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models import Answer, AnswerVote, CommunityMembership, Post, User
from app.posts.renderer import render_tiptap_json
from app.reputation.engine import award_rep
from app.votes.schemas import VoteRequest, VoteResponse

from .schemas import (
    AnswerListResponse,
    AnswerResponse,
    CreateAnswerRequest,
    RemoveAnswerRequest,
    UpdateAnswerRequest,
)

router = APIRouter(tags=["answers"])


def _answer_response(answer: Answer, *, author: User | None = None) -> AnswerResponse:
    return AnswerResponse(
        id=answer.id,
        question_id=answer.question_id,
        author_id=answer.author_id,
        author_handle=author.handle if author else None,
        author_display_name=author.display_name if author else None,
        author_avatar_url=author.avatar_url if author else None,
        body_json=answer.body_json if not answer.removed_at else None,
        body_html=answer.body_html if not answer.removed_at else "",
        score=answer.score,
        is_accepted=answer.is_accepted,
        accepted_at=answer.accepted_at,
        deleted_at=answer.deleted_at,
        removed_at=answer.removed_at,
        created_at=answer.created_at,
        updated_at=answer.updated_at,
    )


async def _get_membership(
    session: AsyncSession, community_id: uuid.UUID, user_id: uuid.UUID
) -> CommunityMembership | None:
    result = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


@router.post("/api/posts/{post_id}/answers", response_model=AnswerResponse, status_code=201)
async def create_answer(
    post_id: uuid.UUID,
    body: CreateAnswerRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.post_type != "question":
        raise HTTPException(status_code=400, detail="Can only answer questions")

    membership = await _get_membership(session, post.community_id, user.id)
    if not membership or membership.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to answer")

    body_html = render_tiptap_json(body.body_json)

    answer = Answer(
        question_id=post.id,
        author_id=user.id,
        body_json=body.body_json,
        body_html=body_html,
    )
    session.add(answer)

    post.answer_count = post.answer_count + 1
    await session.flush()
    await session.refresh(answer)

    from app.reputation.badges import check_badges

    await check_badges(session, user.id)

    return _answer_response(answer, author=user)


@router.get("/api/posts/{post_id}/answers", response_model=AnswerListResponse)
async def list_answers(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(Post, post_id)
    if not post or post.deleted_at:
        raise HTTPException(status_code=404, detail="Post not found")

    stmt = (
        select(Answer, User)
        .outerjoin(User, Answer.author_id == User.id)
        .where(Answer.question_id == post_id, Answer.deleted_at.is_(None))
        .order_by(Answer.is_accepted.desc(), Answer.score.desc(), Answer.created_at.asc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    answers = [_answer_response(row.Answer, author=row.User) for row in rows]
    return AnswerListResponse(answers=answers, count=len(answers))


@router.patch("/api/answers/{answer_id}", response_model=AnswerResponse)
async def update_answer(
    answer_id: uuid.UUID,
    body: UpdateAnswerRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")
    if answer.removed_at:
        raise HTTPException(status_code=403, detail="Cannot edit a removed answer")
    if answer.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the author can edit")

    answer.body_json = body.body_json
    answer.body_html = render_tiptap_json(body.body_json)
    await session.flush()
    await session.refresh(answer)

    return _answer_response(answer, author=user)


@router.delete("/api/answers/{answer_id}", status_code=200)
async def delete_answer(
    answer_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")
    if answer.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the author can delete")

    answer.deleted_at = datetime.now(UTC)

    post = await session.get(Post, answer.question_id)
    if post:
        post.answer_count = max(0, post.answer_count - 1)
        if answer.is_accepted:
            post.has_accepted_answer = False
            answer.is_accepted = False
            answer.accepted_at = None

    return {"status": "deleted"}


@router.post("/api/answers/{answer_id}/remove", response_model=AnswerResponse)
async def remove_answer(
    answer_id: uuid.UUID,
    body: RemoveAnswerRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")

    post = await session.get(Post, answer.question_id)
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    if user.role != "admin":
        membership = await _get_membership(session, post.community_id, user.id)
        if not membership or membership.role not in ("mod", "owner"):
            raise HTTPException(status_code=403, detail="Only mods, owners, or admins can remove")

    answer.removed_at = datetime.now(UTC)
    answer.removed_by = user.id
    answer.removed_reason = body.reason
    await session.flush()
    await session.refresh(answer)

    author = await session.get(User, answer.author_id) if answer.author_id else None
    return _answer_response(answer, author=author)


@router.post("/api/answers/{answer_id}/accept", status_code=200)
async def accept_answer(
    answer_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")

    post = await session.get(Post, answer.question_id)
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the question author can accept")

    # Unaccept any previously accepted answer on this question
    await session.execute(
        update(Answer)
        .where(Answer.question_id == post.id, Answer.is_accepted.is_(True))
        .values(is_accepted=False, accepted_at=None)
    )

    answer.is_accepted = True
    answer.accepted_at = datetime.now(UTC)
    post.has_accepted_answer = True

    if answer.author_id:
        await award_rep(session, answer.author_id, "answer_accepted", answer.id)
    if post.author_id:
        await award_rep(session, post.author_id, "accept_answer", answer.id)

    await session.flush()
    return {"status": "accepted"}


@router.delete("/api/answers/{answer_id}/accept", status_code=200)
async def unaccept_answer(
    answer_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")

    post = await session.get(Post, answer.question_id)
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the question author can unaccept")

    if not answer.is_accepted:
        raise HTTPException(status_code=400, detail="Answer is not accepted")

    answer.is_accepted = False
    answer.accepted_at = None
    post.has_accepted_answer = False

    if answer.author_id:
        await award_rep(
            session,
            answer.author_id,
            "answer_accepted",
            answer.id,
            reverse=True,
        )
    if post.author_id:
        await award_rep(
            session,
            post.author_id,
            "accept_answer",
            answer.id,
            reverse=True,
        )

    await session.flush()
    return {"status": "unaccepted"}


@router.post("/api/answers/{answer_id}/vote", response_model=VoteResponse)
async def vote_answer(
    answer_id: uuid.UUID,
    body: VoteRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    value = body.value

    answer = await session.get(Answer, answer_id)
    if not answer or answer.deleted_at:
        raise HTTPException(status_code=404, detail="Answer not found")
    if answer.removed_at:
        raise HTTPException(status_code=403, detail="Cannot vote on a removed answer")
    if answer.author_id == user.id:
        raise HTTPException(status_code=403, detail="Cannot vote on your own answer")

    post = await session.get(Post, answer.question_id)
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    membership = await _get_membership(session, post.community_id, user.id)
    if not membership or membership.banned_at:
        raise HTTPException(status_code=403, detail="Must be a member to vote")

    old_vote_q = select(AnswerVote.value).where(
        AnswerVote.user_id == user.id,
        AnswerVote.answer_id == answer_id,
    )
    old_result = await session.execute(old_vote_q)
    old_val = old_result.scalar_one_or_none()

    if value == 0:
        await session.execute(
            delete(AnswerVote).where(
                AnswerVote.user_id == user.id,
                AnswerVote.answer_id == answer_id,
            )
        )
    else:
        stmt = pg_insert(AnswerVote).values(
            id=uuid.uuid4(),
            user_id=user.id,
            answer_id=answer_id,
            value=value,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_answer_votes_answer_user",
            set_={"value": value},
        )
        await session.execute(stmt)

    if answer.author_id:
        if old_val == 1:
            await award_rep(
                session,
                answer.author_id,
                "answer_upvoted",
                answer.id,
                reverse=True,
            )
        elif old_val == -1:
            await award_rep(
                session,
                answer.author_id,
                "answer_downvoted",
                answer.id,
                reverse=True,
            )
            await award_rep(
                session,
                user.id,
                "downvote_answer_cost",
                answer.id,
                reverse=True,
            )
        if value == 1:
            await award_rep(
                session,
                answer.author_id,
                "answer_upvoted",
                answer.id,
            )
        elif value == -1:
            await award_rep(
                session,
                answer.author_id,
                "answer_downvoted",
                answer.id,
            )
            await award_rep(
                session,
                user.id,
                "downvote_answer_cost",
                answer.id,
            )

    await session.flush()
    await session.refresh(answer)

    return VoteResponse(score=answer.score, user_vote=value)
