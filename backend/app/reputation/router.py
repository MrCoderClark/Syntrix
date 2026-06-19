from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.models.reputation import Badge, ReputationEvent, UserBadge

from .schemas import (
    BadgeResponse,
    RepEventResponse,
    UserBadgeResponse,
    UserRepResponse,
)

router = APIRouter(prefix="/api/users", tags=["reputation"])


@router.get("/{handle}/reputation", response_model=UserRepResponse)
async def get_user_reputation(
    handle: str,
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(User).where(User.handle == handle))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    events_q = (
        select(ReputationEvent)
        .where(ReputationEvent.user_id == user.id)
        .order_by(ReputationEvent.created_at.desc())
        .limit(limit)
    )
    events_result = await session.execute(events_q)
    events = events_result.scalars().all()

    badges_q = (
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
        .order_by(UserBadge.awarded_at.desc())
    )
    badges_result = await session.execute(badges_q)
    badge_rows = badges_result.all()

    return UserRepResponse(
        reputation=user.reputation,
        events=[
            RepEventResponse(
                id=str(e.id),
                event_type=e.event_type,
                delta=e.delta,
                source_id=(str(e.source_id) if e.source_id else None),
                created_at=e.created_at,
            )
            for e in events
        ],
        badges=[
            UserBadgeResponse(
                badge=BadgeResponse(
                    slug=row.Badge.slug,
                    name=row.Badge.name,
                    description=row.Badge.description,
                    icon=row.Badge.icon,
                    tier=row.Badge.tier,
                ),
                awarded_at=row.UserBadge.awarded_at,
            )
            for row in badge_rows
        ],
    )
