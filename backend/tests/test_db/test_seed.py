"""Demo-account seeding: creation, hashing, idempotency, skip behaviour."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.security import verify_password
from app.config import settings
from app.db import seed
from app.models.user import TIER_DEMO, UserModel
from app.services.user_repository import PostgresUserRepository

PASSWORD = "SeedPass123"


@pytest.fixture
def demo_email(monkeypatch, session_factory) -> str:
    """Seed a unique demo account inside the test transaction."""
    monkeypatch.setattr(seed, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(settings, "demo_user_email", f"seed-{uuid4().hex[:12]}@x.dev")
    monkeypatch.setattr(settings, "demo_user_password", PASSWORD)
    monkeypatch.setattr(settings, "demo_user_name", "Seeded Demo")
    assert settings.demo_user_email is not None
    return settings.demo_user_email


async def _count_users(
    email: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    async with session_factory() as session:
        return (
            await session.scalar(
                select(func.count())
                .select_from(UserModel)
                .where(UserModel.email == email)
            )
        ) or 0


async def test_seed_creates_demo_user_with_hashed_password(
    demo_email: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed.seed_demo_user()

    async with session_factory() as session:
        user = await PostgresUserRepository(session).get_by_email(demo_email)

    assert user is not None
    assert user.name == "Seeded Demo"
    assert user.tier == TIER_DEMO
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)


async def test_seed_upgrades_existing_demo_user_to_demo_tier(
    demo_email: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Accounts seeded before the demo tier existed get reconciled."""
    async with session_factory() as session:
        await PostgresUserRepository(session).create(
            email=demo_email, name="Old Demo", password_hash="hash"
        )

    await seed.seed_demo_user()

    async with session_factory() as session:
        user = await PostgresUserRepository(session).get_by_email(demo_email)

    assert user is not None
    assert user.tier == TIER_DEMO


async def test_seed_is_idempotent(
    demo_email: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed.seed_demo_user()
    await seed.seed_demo_user()

    assert await _count_users(demo_email, session_factory) == 1


async def test_seed_skips_when_credentials_are_not_configured(
    monkeypatch,
    session_factory,
) -> None:
    monkeypatch.setattr(seed, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(settings, "demo_user_email", None)
    monkeypatch.setattr(settings, "demo_user_password", None)

    await seed.seed_demo_user()  # must not raise or write
