"""PostgresUserRepository contract tests."""

from uuid import uuid4

import pytest

from app.services.user_repository import PostgresUserRepository


async def test_create_persists_user(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    email = email_factory("repo")

    created = await user_repository.create(
        email=email,
        name="Repo User",
        password_hash="bcrypt-hash",
    )

    assert created.id is not None
    assert created.email == email
    assert created.tier == "free"
    assert created.created_at is not None

    fetched = await user_repository.get_by_email(email)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.password_hash == "bcrypt-hash"


async def test_create_persists_custom_tier(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    created = await user_repository.create(
        email=email_factory("tier"),
        name="Tiered User",
        password_hash="hash",
        tier="demo",
    )

    assert created.tier == "demo"
    fetched = await user_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.tier == "demo"


async def test_update_tier_persists(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    created = await user_repository.create(
        email=email_factory("retitle"),
        name="Retitle User",
        password_hash="hash",
    )
    assert created.tier == "free"

    updated = await user_repository.update_tier(created.id, "pro")

    assert updated is not None
    assert updated.tier == "pro"
    fetched = await user_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.tier == "pro"


async def test_update_tier_unknown_id_returns_none(
    user_repository: PostgresUserRepository,
) -> None:
    assert await user_repository.update_tier(uuid4(), "pro") is None


async def test_email_lookup_ignores_case_and_whitespace(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    email = email_factory("case")
    created = await user_repository.create(
        email=email,
        name="Case Test",
        password_hash="hash",
    )

    fetched = await user_repository.get_by_email(f"  {email.upper()}  ")

    assert fetched is not None
    assert fetched.id == created.id


async def test_get_by_id_returns_user(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    created = await user_repository.create(
        email=email_factory("byid"),
        name="ById Test",
        password_hash="hash",
    )

    fetched = await user_repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.email == created.email


async def test_get_by_id_unknown_returns_none(
    user_repository: PostgresUserRepository,
) -> None:
    assert await user_repository.get_by_id(uuid4()) is None


async def test_get_by_email_unknown_returns_none(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    assert await user_repository.get_by_email(email_factory("missing")) is None


async def test_duplicate_email_raises_value_error(
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    email = email_factory("dupe")
    await user_repository.create(email=email, name="First", password_hash="hash")

    with pytest.raises(ValueError, match="email already exists"):
        await user_repository.create(
            email=email.upper(),
            name="Second",
            password_hash="hash",
        )
