import asyncio
import platform
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.engine import async_engine

if platform.system() == "Windows":

    @pytest.fixture(scope="session")
    def event_loop_policy():
        return asyncio.WindowsSelectorEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _verify_engine_reachable():
    try:
        async with async_engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except Exception as exc:
        pytest.exit(
            f"Database not reachable. Check PG_* env vars and Supabase stack. Error: {exc!r}",
            returncode=2,
        )
    yield


@pytest_asyncio.fixture
async def db_conn() -> AsyncIterator[AsyncConnection]:
    async with async_engine.connect() as conn:
        await conn.exec_driver_sql("DEALLOCATE ALL")
        await conn.rollback()
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()
