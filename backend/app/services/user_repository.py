"""User repository abstraction.

The rest of the app depends on the ``UserRepository`` protocol only.
``USER_STORE=postgres`` selects the real database, ``USER_STORE=memory``
keeps the zero-infra store used by tests — selected purely via the
environment, no code changes anywhere else.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import UserModel


@dataclass
class User:
    """Domain user record (storage-agnostic)."""

    email: str
    name: str
    password_hash: str
    tier: str = field(default="free")
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class UserRepository(Protocol):
    """Storage contract for users. Implementations must be async."""

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def create(self, *, email: str, name: str, password_hash: str) -> User: ...


def normalize_email(email: str) -> str:
    """Canonical email form used for lookups and unique constraints."""
    return email.strip().lower()


def _to_domain(user: UserModel) -> User:
    """Map an ORM row to the domain dataclass."""
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        password_hash=user.password_hash,
        tier=user.tier,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class InMemoryUserRepository:
    """Thread-safe in-memory user store for local development and tests.

    Data is lost on restart — use ``USER_STORE=postgres`` for persistence.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_email: dict[str, User] = {}
        self._by_id: dict[UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        async with self._lock:
            return self._by_email.get(normalize_email(email))

    async def get_by_id(self, user_id: UUID) -> User | None:
        async with self._lock:
            return self._by_id.get(user_id)

    async def create(self, *, email: str, name: str, password_hash: str) -> User:
        async with self._lock:
            normalized = normalize_email(email)
            if normalized in self._by_email:
                raise ValueError("email already exists")
            user = User(
                email=normalized,
                name=name,
                password_hash=password_hash,
            )
            self._by_email[normalized] = user
            self._by_id[user.id] = user
            return user


class PostgresUserRepository:
    """PostgreSQL-backed users, using the request's async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == normalize_email(email))
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserModel, user_id)
        return _to_domain(row) if row is not None else None

    async def create(self, *, email: str, name: str, password_hash: str) -> User:
        """Insert a user and commit.

        Raises ``ValueError`` when the email is taken — the same contract as
        the in-memory store, so the auth service handles both identically.
        """
        row = UserModel(
            email=normalize_email(email),
            name=name,
            password_hash=password_hash,
        )
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError("email already exists") from exc
        await self._session.refresh(row)
        return _to_domain(row)


_repository_instance: UserRepository | None = None


def get_user_repository(session: AsyncSession | None = None) -> UserRepository:
    """Return the configured user store.

    ``USER_STORE=postgres`` needs a session (injected per request via
    ``get_db``); the in-memory store is a process-wide singleton so every
    request sees the same data.
    """
    global _repository_instance
    if settings.user_store == "postgres":
        if session is None:
            raise RuntimeError("USER_STORE=postgres requires a database session")
        return PostgresUserRepository(session)
    if _repository_instance is None:
        _repository_instance = InMemoryUserRepository()
    return _repository_instance
