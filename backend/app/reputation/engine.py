from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reputation import ReputationEvent

from .badges import check_badges

REP_VALUES: dict[str, int] = {
    "answer_upvoted": 10,
    "answer_downvoted": -2,
    "answer_accepted": 15,
    "accept_answer": 2,
    "question_upvoted": 5,
    "question_downvoted": -2,
    "downvote_answer_cost": -1,
}


async def award_rep(
    session: AsyncSession,
    user_id: uuid.UUID,
    event_type: str,
    source_id: uuid.UUID | None = None,
    *,
    reverse: bool = False,
) -> None:
    """Record a reputation event and, on forward events, check badge criteria."""
    # 1. Look up delta; bail early if unknown or zero
    delta = REP_VALUES.get(event_type, 0)
    if delta == 0:
        return

    # 2. Negate when reversing (e.g. un-upvote)
    if reverse:
        delta = -delta

    # 3. Insert the reputation event
    session.add(
        ReputationEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            delta=delta,
            source_id=source_id,
        )
    )

    # 4. Flush so the row is visible to subsequent queries in this transaction
    await session.flush()

    # 5. Only check badges on forward (positive-action) events
    if not reverse:
        await check_badges(session, user_id)
