import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.auth.rate_limit import check_rate_limit


@pytest.mark.asyncio
async def test_rate_limit_allows_within_budget(db_conn: AsyncConnection):
    allowed = await check_rate_limit(
        db_conn, key="test:allow", max_tokens=10, refill_rate=1.0, cost=1
    )
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limit_denies_when_exhausted(db_conn: AsyncConnection):
    for _ in range(5):
        await check_rate_limit(db_conn, key="test:exhaust", max_tokens=5, refill_rate=0.0, cost=1)
    denied = await check_rate_limit(
        db_conn, key="test:exhaust", max_tokens=5, refill_rate=0.0, cost=1
    )
    assert denied is False


@pytest.mark.asyncio
async def test_rate_limit_creates_bucket_on_first_call(db_conn: AsyncConnection):
    key = "test:create"
    await check_rate_limit(db_conn, key=key, max_tokens=10, refill_rate=1.0, cost=1)
    result = await db_conn.execute(
        text("SELECT tokens FROM rate_limit_buckets WHERE key = :k"), {"k": key}
    )
    row = result.one()
    assert float(row.tokens) == 9.0
