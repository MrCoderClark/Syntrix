import asyncio
import platform
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
)

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
            f"Database not reachable: {exc!r}",
            returncode=2,
        )
    yield


@pytest_asyncio.fixture
async def db_conn() -> AsyncIterator[AsyncConnection]:
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()


@pytest_asyncio.fixture
async def db_session(
    db_conn: AsyncConnection,
) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(bind=db_conn, expire_on_commit=False)
    async with session_maker() as session:
        yield session
