from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    tokens: Mapped[float] = mapped_column(Numeric, nullable=False)
    max_tokens: Mapped[float] = mapped_column(Numeric, nullable=False)
    refill_rate: Mapped[float] = mapped_column(Numeric, nullable=False)
    refilled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
