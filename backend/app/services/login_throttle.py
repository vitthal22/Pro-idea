"""Login throttling (brute-force protection).

Counts failed logins per key (email + client) inside a sliding window. The
in-memory implementation is enough for the single-worker MVP; a Redis-backed
implementation can be dropped in behind the same protocol when the API runs
with several workers.
"""

import time
from typing import Protocol


class LoginThrottle(Protocol):
    """Storage contract for failed-login counting."""

    def is_blocked(self, key: str, *, timestamp: float | None = None) -> bool: ...

    def record_failure(
        self,
        key: str,
        *,
        timestamp: float | None = None,
    ) -> None: ...

    def reset(self, key: str) -> None: ...


class InMemoryLoginThrottle:
    """Per-process sliding-window failure counter."""

    def __init__(self, *, max_failures: int, window_seconds: int) -> None:
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}

    def is_blocked(self, key: str, *, timestamp: float | None = None) -> bool:
        """True when the key hit the failure limit inside the window."""
        return len(self._recent_failures(key, timestamp)) >= self._max_failures

    def record_failure(
        self,
        key: str,
        *,
        timestamp: float | None = None,
    ) -> None:
        """Record one failed attempt, pruning expired entries first."""
        recent = self._recent_failures(key, timestamp)
        recent.append(timestamp if timestamp is not None else time.monotonic())
        self._failures[key] = recent

    def reset(self, key: str) -> None:
        """Forget the key (successful login)."""
        self._failures.pop(key, None)

    def _recent_failures(
        self,
        key: str,
        timestamp: float | None,
    ) -> list[float]:
        now = timestamp if timestamp is not None else time.monotonic()
        cutoff = now - self._window_seconds
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        elif key in self._failures:
            del self._failures[key]
        return recent
