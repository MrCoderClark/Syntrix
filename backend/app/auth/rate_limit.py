from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def check_rate_limit(
    conn: AsyncConnection,
    *,
    key: str,
    max_tokens: float,
    refill_rate: float,
    cost: float = 1.0,
) -> bool:
    result = await conn.execute(
        text(
            """
            INSERT INTO rate_limit_buckets (key, tokens, max_tokens, refill_rate, refilled_at)
            VALUES (:key, :max_tokens - :cost, :max_tokens, :refill_rate, now())
            ON CONFLICT (key) DO UPDATE SET
                tokens = LEAST(
                    rate_limit_buckets.max_tokens,
                    rate_limit_buckets.tokens
                        + rate_limit_buckets.refill_rate
                        * EXTRACT(EPOCH FROM now() - rate_limit_buckets.refilled_at)
                ) - :cost,
                refilled_at = now()
            WHERE LEAST(
                rate_limit_buckets.max_tokens,
                rate_limit_buckets.tokens
                    + rate_limit_buckets.refill_rate
                    * EXTRACT(EPOCH FROM now() - rate_limit_buckets.refilled_at)
            ) >= :cost
            RETURNING tokens
        """
        ),
        {"key": key, "max_tokens": max_tokens, "refill_rate": refill_rate, "cost": cost},
    )
    row = result.first()
    return row is not None
