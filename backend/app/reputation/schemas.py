from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RepEventResponse(BaseModel):
    id: str
    event_type: str
    delta: int
    source_id: str | None
    created_at: datetime


class BadgeResponse(BaseModel):
    slug: str
    name: str
    description: str | None
    icon: str | None
    tier: str


class UserBadgeResponse(BaseModel):
    badge: BadgeResponse
    awarded_at: datetime


class UserRepResponse(BaseModel):
    reputation: int
    events: list[RepEventResponse]
    badges: list[UserBadgeResponse]
