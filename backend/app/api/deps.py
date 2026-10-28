"""FastAPI dependencies and auth cookie helpers."""

from collections.abc import AsyncIterator

import jwt
from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AuthenticationError
from app.common.security import decode_token
from app.config import settings
from app.db.session import get_session_factory
from app.services.auth import AuthService
from app.services.login_throttle import InMemoryLoginThrottle, LoginThrottle
from app.services.resume import ResumeService
from app.services.token_denylist import get_token_denylist
from app.services.user_repository import (
    User,
    UserRepository,
    get_user_repository,
)
from app.storage.base import Storage
from app.storage.local_storage import LocalStorage

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"
LOGIN_THROTTLE_WINDOW_SECONDS = 3600


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session (closed when the request ends)."""
    async with get_session_factory()() as session:
        yield session


async def get_user_repo(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Request-scoped user repository (env-selected backend)."""
    return get_user_repository(session)


_storage_instance: Storage | None = None


def get_storage() -> Storage:
    """Return the configured file storage (process-wide singleton)."""
    global _storage_instance
    if _storage_instance is None:
        if settings.storage_backend != "local":
            raise NotImplementedError(
                f"STORAGE_BACKEND={settings.storage_backend!r} is not "
                "implemented; use 'local'."
            )
        _storage_instance = LocalStorage()
    return _storage_instance


def get_resume_service(
    session: AsyncSession = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> ResumeService:
    """Resume use cases bound to the request session and configured storage."""
    return ResumeService(session, storage, settings.max_file_size_mb)


_login_throttle_instance: LoginThrottle | None = None


def get_login_throttle() -> LoginThrottle:
    """Return the process-wide failed-login counter."""
    global _login_throttle_instance
    if _login_throttle_instance is None:
        _login_throttle_instance = InMemoryLoginThrottle(
            max_failures=settings.login_rate_limit_per_hour,
            window_seconds=LOGIN_THROTTLE_WINDOW_SECONDS,
        )
    return _login_throttle_instance


def get_auth_service(
    repository: UserRepository = Depends(get_user_repo),
    throttle: LoginThrottle = Depends(get_login_throttle),
) -> AuthService:
    """Build an AuthService bound to the configured stores."""
    return AuthService(repository, get_token_denylist(), throttle)


async def get_current_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repo),
) -> User:
    """Resolve the current user from the Bearer access token."""
    auth_header = request.headers.get("Authorization") or ""
    scheme, _, credentials = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        raise AuthenticationError(message="Not authenticated")

    try:
        payload = decode_token(credentials, expected_type="access")
    except (jwt.PyJWTError, ValueError) as exc:
        raise AuthenticationError(message="Invalid or expired token") from exc

    user = await repository.get_by_id(payload.user_id)
    if user is None:
        raise AuthenticationError(message="User no longer exists")
    return user


async def get_refresh_token(request: Request) -> str | None:
    """Read the refresh token from its HttpOnly cookie, if present."""
    return request.cookies.get(REFRESH_COOKIE_NAME)


def set_refresh_cookie(response: Response, token: str) -> None:
    """Attach the refresh token as an HttpOnly, path-scoped cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path=REFRESH_COOKIE_PATH,
        max_age=settings.jwt_refresh_expire_days * 24 * 3600,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh cookie (must match the path it was set with)."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )
