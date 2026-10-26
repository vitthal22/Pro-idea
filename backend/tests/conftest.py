"""Shared pytest fixtures.

Tests run against a **real PostgreSQL** database (never SQLite), using the
same tables and migrations as production. Every test is wrapped in an outer
transaction that is rolled back, so rows created by a test never survive it
and the dev database (including the seeded demo user) is left untouched.

Requires the database in ``DB_*`` / ``DATABASE_URL`` to be reachable; the
session fixture applies migrations first.
"""

from collections.abc import AsyncIterator, Callable
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.config import settings
from app.main import app
from app.services.token_denylist import InMemoryTokenDenylist
from app.services.user_repository import PostgresUserRepository


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Apply migrations once so the ``users`` table exists."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(scope="session", autouse=True)
def postgres_user_store() -> None:
    """These tests exercise the real database, not the in-memory store."""
    settings.user_store = "postgres"


@pytest.fixture
async def db_connection() -> AsyncIterator[AsyncConnection]:
    """Open a connection whose transaction is rolled back after the test."""
    engine = create_async_engine(settings.database_dsn, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def session_factory(
    db_connection: AsyncConnection,
) -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the test connection.

    ``create_savepoint`` turns the repository's ``commit()`` into a savepoint
    release, so service-level code works unchanged while the outer rollback
    still discards everything.
    """
    return async_sessionmaker(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Request-scoped session equivalent, isolated to the test."""
    async with session_factory() as session:
        yield session


@pytest.fixture
def user_repository(db_session: AsyncSession) -> PostgresUserRepository:
    """Repository wired to the test session."""
    return PostgresUserRepository(db_session)


@pytest.fixture
def denylist() -> InMemoryTokenDenylist:
    """Fresh revocation store per test."""
    return InMemoryTokenDenylist()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client for the app, sharing the test's transaction."""

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
    app.dependency_overrides.clear()


@pytest.fixture
def email_factory() -> Callable[[str], str]:
    """Generate a unique email per call so tests never collide."""

    def make(prefix: str = "user") -> str:
        return f"{prefix}-{uuid4().hex[:12]}@example.com"

    return make
