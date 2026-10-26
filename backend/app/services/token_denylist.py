"""Refresh-token denylist (logout).

Protocol now, backed by whatever the environment configures later:
``memory`` (default, dev) → ``redis``/``postgres`` when available — the
same env-seam pattern as the user store. Callers never change.
"""

from datetime import UTC, datetime
from typing import Protocol

from app.config import settings


class TokenDenylist(Protocol):
    """Storage contract for revoked refresh tokens."""

    def revoke(self, jti: str, expires_at: datetime) -> None: ...

    def is_revoked(self, jti: str) -> bool: ...


class InMemoryTokenDenylist:
    """In-process denylist for local development.

    Lost on restart — acceptable until Redis/Postgres lands. Expired
    entries are purged on lookup so the map cannot grow unbounded.
    """

    def __init__(self) -> None:
        self._revoked: dict[str, datetime] = {}

    def revoke(self, jti: str, expires_at: datetime) -> None:
        self._revoked[jti] = expires_at

    def is_revoked(self, jti: str) -> bool:
        expires_at = self._revoked.get(jti)
        if expires_at is None:
            return False
        if expires_at <= datetime.now(UTC):
            del self._revoked[jti]  # entry outlived its token
            return False
        return True


_denylist_instance: TokenDenylist | None = None


def get_token_denylist() -> TokenDenylist:
    """Return the configured denylist as a process-wide singleton."""
    global _denylist_instance
    if _denylist_instance is None:
        # settings.denylist_store selects the backend once Redis exists.
        _ = settings.denylist_store
        _denylist_instance = InMemoryTokenDenylist()
    return _denylist_instance
