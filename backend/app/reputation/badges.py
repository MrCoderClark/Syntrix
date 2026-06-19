from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import Answer
from app.models.post import Post
from app.models.reputation import Badge, UserBadge


async def _meets_criteria(
    session: AsyncSession,
    user_id: uuid.UUID,
    criteria: dict,
) -> bool:
    """Return True if the user satisfies all criteria in the criteria dict."""
    for criterion, threshold in criteria.items():
        if criterion == "question_count":
            count_q = await session.execute(
                select(func.count())
                .select_from(Post)
                .where(
                    Post.author_id == user_id,
                    Post.post_type == "question",
                    Post.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < threshold:
                return False

        elif criterion == "answer_count":
            count_q = await session.execute(
                select(func.count())
                .select_from(Answer)
                .where(
                    Answer.author_id == user_id,
                    Answer.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < threshold:
                return False

        elif criterion == "accepted_answer_count":
            count_q = await session.execute(
                select(func.count())
                .select_from(Answer)
                .where(
                    Answer.author_id == user_id,
                    Answer.is_accepted.is_(True),
                    Answer.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < threshold:
                return False

        elif criterion == "questions_with_accepted":
            count_q = await session.execute(
                select(func.count())
                .select_from(Post)
                .where(
                    Post.author_id == user_id,
                    Post.post_type == "question",
                    Post.has_accepted_answer.is_(True),
                    Post.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < threshold:
                return False

        elif criterion == "answer_score_gte":
            # threshold here is the minimum score; count must be >= 1
            count_q = await session.execute(
                select(func.count())
                .select_from(Answer)
                .where(
                    Answer.author_id == user_id,
                    Answer.score >= threshold,
                    Answer.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < 1:
                return False

        elif criterion == "questions_with_score_gte":
            # threshold is the required count; min_score comes from criteria dict (default 1)
            min_score = criteria.get("min_score", 1)
            count_q = await session.execute(
                select(func.count())
                .select_from(Post)
                .where(
                    Post.author_id == user_id,
                    Post.post_type == "question",
                    Post.score >= min_score,
                    Post.deleted_at.is_(None),
                )
            )
            if count_q.scalar_one() < threshold:
                return False

        # skip unknown keys (e.g. "min_score" which is a parameter, not a standalone criterion)

    return True


async def check_badges(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[Badge]:
    """Check all badges and award any newly earned ones. Returns newly awarded badges."""
    # 1. Get the set of badge IDs already owned by this user
    owned_result = await session.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    )
    owned_ids: set[uuid.UUID] = {row[0] for row in owned_result.all()}

    # 2. Fetch all badges
    all_badges_result = await session.execute(select(Badge))
    all_badges: list[Badge] = list(all_badges_result.scalars().all())

    # 3 & 4. For each unowned badge, check criteria and award if met
    newly_awarded: list[Badge] = []
    for badge in all_badges:
        if badge.id in owned_ids:
            continue
        if await _meets_criteria(session, user_id, badge.criteria):
            session.add(
                UserBadge(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    badge_id=badge.id,
                )
            )
            newly_awarded.append(badge)

    return newly_awarded
