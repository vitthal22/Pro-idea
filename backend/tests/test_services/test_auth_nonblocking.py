"""bcrypt must run off the event loop (TDD red phase).

bcrypt costs ~270 ms per verify on this machine. If the service calls it
inline, the whole worker stalls for that time — health checks, other logins
and SSE streams included.
"""

import asyncio
import time

import pytest

from app.api.schemas.auth import LoginRequest, RegisterRequest
from app.common.exceptions import AuthenticationError
from app.services.auth import AuthService
from app.services.token_denylist import InMemoryTokenDenylist
from app.services.user_repository import PostgresUserRepository

PASSWORD = "Secret123"
SLOW_BCRYPT_SECONDS = 0.25
TICK_SECONDS = 0.01


@pytest.fixture
def auth_service(
    user_repository: PostgresUserRepository,
    denylist: InMemoryTokenDenylist,
) -> AuthService:
    return AuthService(user_repository, denylist)


async def test_login_does_not_block_the_event_loop(
    auth_service: AuthService,
    email_factory,
    monkeypatch,
) -> None:
    email = email_factory("nonblocking")
    await auth_service.register(
        RegisterRequest(name="Non Blocking", email=email, password=PASSWORD)
    )

    def slow_verify(password: str, password_hash: str) -> bool:
        time.sleep(SLOW_BCRYPT_SECONDS)
        return False

    monkeypatch.setattr("app.services.auth.verify_password", slow_verify)

    ticks = 0
    running = True

    async def ticker() -> None:
        nonlocal ticks
        while running:
            ticks += 1
            await asyncio.sleep(TICK_SECONDS)

    ticker_task = asyncio.create_task(ticker())
    await asyncio.sleep(0)  # let the ticker start

    with pytest.raises(AuthenticationError):
        await auth_service.login(LoginRequest(email=email, password="WrongPass123"))

    running = False
    await ticker_task

    expected_ticks = int(SLOW_BCRYPT_SECONDS / TICK_SECONDS) // 2
    assert ticks >= expected_ticks, (
        f"event loop was blocked during hashing: only {ticks} ticks "
        f"(expected >= {expected_ticks})"
    )
