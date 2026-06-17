from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func

from app.models import Post

REFERENCE_EPOCH = datetime(2024, 1, 1, tzinfo=UTC)


def hot_score_expr():
    score = Post.score
    age = func.extract("epoch", Post.created_at - REFERENCE_EPOCH)
    return func.sign(score) * func.log(func.greatest(func.abs(score), 1)) + age / 45000.0


def hot_order():
    return [desc(hot_score_expr()), desc(Post.id)]


def new_order():
    return [desc(Post.created_at), desc(Post.id)]


def top_order():
    return [desc(Post.score), desc(Post.created_at), desc(Post.id)]


def top_period_filter(period: str):
    now = datetime.now(UTC)
    cutoffs = {
        "today": now - timedelta(days=1),
        "week": now - timedelta(weeks=1),
        "month": now - timedelta(days=30),
        "all": None,
    }
    cutoff = cutoffs.get(period)
    if cutoff is None:
        return None
    return Post.created_at >= cutoff
