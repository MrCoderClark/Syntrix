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
        connect_args={"options": "-c search_path=syntrix,public"},
    )
    return engine


async_engine: AsyncEngine = _build_async_engine()
