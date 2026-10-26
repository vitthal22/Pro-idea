"""Async database engine and session factory.

The DSN comes from ``Settings.database_dsn`` — nothing is hardcoded, so the
same code runs against local, dev, and prod databases.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine.

    ``pool_pre_ping`` drops dead connections instead of failing a request,
    and the connect timeout bounds a slow/unreachable database so a request
    fails fast with a clean 5xx rather than hanging.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_dsn,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=10,
            connect_args={"timeout": 10},
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield a session outside the request lifecycle (startup, scripts)."""
    async with get_session_factory()() as session:
        yield session


async def dispose_engine() -> None:
    """Close pooled connections (application shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
