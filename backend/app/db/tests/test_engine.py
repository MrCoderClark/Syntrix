import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


@pytest.mark.asyncio
async def test_search_path_is_set_per_connection(db_conn: AsyncConnection):
    result = await db_conn.execute(text("SHOW search_path"))
    value = result.scalar_one()
    assert "syntrix" in value.replace('"', "").replace(" ", "")


@pytest.mark.asyncio
async def test_default_schema_is_syntrix(db_conn: AsyncConnection):
    result = await db_conn.execute(text("SELECT current_schema"))
    assert result.scalar_one() == "syntrix"


@pytest.mark.asyncio
async def test_can_read_alembic_version(db_conn: AsyncConnection):
    result = await db_conn.execute(text("SELECT version_num FROM syntrix.alembic_version"))
    assert result.scalar_one() == "0001_baseline"
