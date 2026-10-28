"""Login throttling — written before the implementation (TDD red phase).

Contract: after ``max_failures`` failed logins for the same email+client,
further attempts return 429 (even with the right password) until the window
passes. A successful login clears the counter, and other accounts are
unaffected.
"""

import pytest

from app.api.deps import get_login_throttle
from app.main import app
from app.services.login_throttle import InMemoryLoginThrottle

LOGIN = "/api/v1/auth/login"
REGISTER = "/api/v1/auth/register"
PASSWORD = "Secret123"
MAX_FAILURES = 3


@pytest.fixture
def throttle(client) -> InMemoryLoginThrottle:
    """Install a fresh, fast-expiring-in-test throttle for this test."""
    limiter = InMemoryLoginThrottle(
        max_failures=MAX_FAILURES,
        window_seconds=3600,
    )
    app.dependency_overrides[get_login_throttle] = lambda: limiter
    return limiter


async def _register(client, email: str) -> None:
    response = await client.post(
        REGISTER,
        json={"name": "Throttle Test", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text


async def _wrong_login(client, email: str):
    return await client.post(
        LOGIN,
        json={"email": email, "password": "DefinitelyWrong1"},
    )


async def test_blocks_after_max_failures(client, throttle, email_factory) -> None:
    email = email_factory("throttle")
    await _register(client, email)

    for _ in range(MAX_FAILURES):
        assert (await _wrong_login(client, email)).status_code == 401

    blocked = await _wrong_login(client, email)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"


async def test_block_applies_even_with_the_correct_password(
    client,
    throttle,
    email_factory,
) -> None:
    email = email_factory("throttle-ok")
    await _register(client, email)
    for _ in range(MAX_FAILURES):
        await _wrong_login(client, email)

    response = await client.post(
        LOGIN,
        json={"email": email, "password": PASSWORD},
    )

    assert response.status_code == 429


async def test_successful_login_resets_the_counter(
    client,
    throttle,
    email_factory,
) -> None:
    email = email_factory("throttle-reset")
    await _register(client, email)
    for _ in range(MAX_FAILURES - 1):
        await _wrong_login(client, email)

    success = await client.post(LOGIN, json={"email": email, "password": PASSWORD})
    assert success.status_code == 200

    for _ in range(MAX_FAILURES):
        assert (await _wrong_login(client, email)).status_code == 401


async def test_throttling_is_scoped_to_the_account(
    client,
    throttle,
    email_factory,
) -> None:
    blocked_email = email_factory("throttle-a")
    other_email = email_factory("throttle-b")
    await _register(client, blocked_email)
    await _register(client, other_email)
    for _ in range(MAX_FAILURES):
        await _wrong_login(client, blocked_email)
    assert (await _wrong_login(client, blocked_email)).status_code == 429

    other = await client.post(
        LOGIN,
        json={"email": other_email, "password": PASSWORD},
    )

    assert other.status_code == 200


def test_window_prunes_old_failures() -> None:
    limiter = InMemoryLoginThrottle(max_failures=2, window_seconds=60)
    key = "someone@example.com|127.0.0.1"

    limiter.record_failure(key, timestamp=1000.0)
    limiter.record_failure(key, timestamp=1001.0)
    assert limiter.is_blocked(key, timestamp=1002.0) is True

    # Outside the 60s window the earlier failures no longer count.
    assert limiter.is_blocked(key, timestamp=1070.0) is False


def test_reset_clears_the_key() -> None:
    limiter = InMemoryLoginThrottle(max_failures=1, window_seconds=60)
    key = "someone@example.com|127.0.0.1"

    limiter.record_failure(key, timestamp=1000.0)
    assert limiter.is_blocked(key, timestamp=1000.5) is True

    limiter.reset(key)
    assert limiter.is_blocked(key, timestamp=1000.5) is False
