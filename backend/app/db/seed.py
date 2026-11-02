"""Idempotent demo-account seeding.

Runs at application startup. The demo credentials come from Settings
(``DEMO_USER_EMAIL`` / ``DEMO_USER_PASSWORD``) — never hardcoded — so each
environment can seed its own account or skip seeding entirely.
"""

import asyncpg
from sqlalchemy.exc import SQLAlchemyError

from app.common.logging import app_logger
from app.common.security import hash_password
from app.config import settings
from app.db.session import get_session_factory
from app.models.user import TIER_DEMO
from app.services.user_repository import get_user_repository


async def seed_demo_user() -> None:
    """Create the demo account if it does not exist yet.

    The account sits on the unlimited ``TIER_DEMO`` tier so the walkthrough
    never hits the per-tier daily cap. Startup must never fail because of
    the seed: an unreachable database or an already-taken email is logged
    and the app keeps running (login simply fails until the database is
    available).
    """
    email = settings.demo_user_email
    password = settings.demo_user_password
    if not email or not password:
        app_logger.info("Demo user seeding skipped (not configured)")
        return

    try:
        async with get_session_factory()() as session:
            repository = get_user_repository(session)
            existing = await repository.get_by_email(email)
            if existing is not None:
                if existing.tier != TIER_DEMO:
                    # Accounts created before the demo tier existed.
                    await repository.update_tier(existing.id, TIER_DEMO)
                    app_logger.info(
                        "Demo user %s moved to the unlimited '%s' tier",
                        email,
                        TIER_DEMO,
                    )
                else:
                    app_logger.info("Demo user already exists: %s", email)
                return
            await repository.create(
                email=email,
                name=settings.demo_user_name,
                password_hash=hash_password(password),
                tier=TIER_DEMO,
            )
    except ValueError:
        app_logger.info("Demo user already exists: %s", email)
        return
    except (SQLAlchemyError, OSError, asyncpg.PostgresError) as exc:
        app_logger.warning(
            "Demo user seeding failed (%s) — the app will still start", exc
        )
        return

    app_logger.info("Demo user created: %s", email)
