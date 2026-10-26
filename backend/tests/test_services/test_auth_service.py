"""AuthService behaviour against the real database."""

import pytest

from app.api.schemas.auth import LoginRequest, RegisterRequest
from app.common.exceptions import AuthenticationError, ConflictError
from app.services.auth import AuthService
from app.services.token_denylist import InMemoryTokenDenylist
from app.services.user_repository import PostgresUserRepository

PASSWORD = "Secret123"
INVALID_CREDENTIALS = "Invalid email or password"


@pytest.fixture
def auth_service(
    user_repository: PostgresUserRepository,
    denylist: InMemoryTokenDenylist,
) -> AuthService:
    return AuthService(user_repository, denylist)


def _registration(email: str, password: str = PASSWORD) -> RegisterRequest:
    return RegisterRequest(name="Service Test", email=email, password=password)


def _login(email: str, password: str = PASSWORD) -> LoginRequest:
    return LoginRequest(email=email, password=password)


async def test_register_creates_user_and_session(
    auth_service: AuthService,
    user_repository: PostgresUserRepository,
    email_factory,
) -> None:
    email = email_factory("reg")

    session = await auth_service.register(_registration(email))

    assert session.tokens.access_token
    assert session.tokens.expires_in > 0
    assert session.refresh_token
    assert session.user.email == email
    stored = await user_repository.get_by_email(email)
    assert stored is not None
    assert stored.password_hash != PASSWORD


async def test_register_duplicate_email_raises_conflict(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("regdup")
    await auth_service.register(_registration(email))

    with pytest.raises(ConflictError):
        await auth_service.register(_registration(email))


async def test_login_with_valid_credentials(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("login")
    await auth_service.register(_registration(email))

    session = await auth_service.login(_login(email))

    assert session.user.email == email
    assert session.refresh_token


async def test_login_wrong_password_raises_generic_error(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("badpw")
    await auth_service.register(_registration(email))

    with pytest.raises(AuthenticationError) as exc:
        await auth_service.login(_login(email, password="WrongPass123"))

    assert exc.value.message == INVALID_CREDENTIALS


async def test_login_unknown_email_uses_same_message(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("unknown")

    with pytest.raises(AuthenticationError) as exc:
        await auth_service.login(_login(email))

    assert exc.value.message == INVALID_CREDENTIALS


async def test_refresh_returns_new_session(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("refresh")
    session = await auth_service.register(_registration(email))

    refreshed = await auth_service.refresh(session.refresh_token)

    assert refreshed.user.email == email
    assert refreshed.refresh_token != session.refresh_token
    assert refreshed.tokens.access_token


async def test_refresh_after_revoke_is_rejected(
    auth_service: AuthService,
    email_factory,
) -> None:
    email = email_factory("revoked")
    session = await auth_service.register(_registration(email))
    await auth_service.revoke(session.refresh_token)

    with pytest.raises(AuthenticationError, match="revoked"):
        await auth_service.refresh(session.refresh_token)


async def test_refresh_without_token_is_rejected(auth_service: AuthService) -> None:
    with pytest.raises(AuthenticationError, match="Missing refresh token"):
        await auth_service.refresh(None)


async def test_revoke_with_invalid_token_is_silent(auth_service: AuthService) -> None:
    await auth_service.revoke("not-a-real-token")
