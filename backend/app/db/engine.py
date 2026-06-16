from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings


def _build_async_engine() -> AsyncEngine:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=5,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_search_path(dbapi_conn, _conn_record):
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("SET search_path TO syntrix, public")
        finally:
            cursor.close()

    return engine


async_engine: AsyncEngine = _build_async_engine()
