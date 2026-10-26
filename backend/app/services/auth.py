"""Authentication business logic.

No HTTP concerns here — routers pass payloads in and receive domain
objects/schemas. Cookies live in the router (HTTP layer).
"""

from dataclasses import dataclass
from uuid import UUID

import jwt

from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.common.exceptions import AuthenticationError, ConflictError
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.services.token_denylist import TokenDenylist
from app.services.user_repository import User, UserRepository


@dataclass(frozen=True)
class AuthSession:
    """Everything the HTTP layer needs to start or continue a session."""

    tokens: TokenResponse
    refresh_token: str
    user: User


class AuthService:
    """Auth use cases operating on a UserRepository."""

    def __init__(
        self,
        repository: UserRepository,
        denylist: TokenDenylist,
    ) -> None:
        self._repository = repository
        self._denylist = denylist

    async def register(self, payload: RegisterRequest) -> AuthSession:
        """Create an account and start a session.

        Raises ``ConflictError`` if the email is already registered.
        """
        existing = await self._repository.get_by_email(payload.email)
        if existing is not None:
            raise ConflictError(
                message="An account with this email already exists",
                details={"email": payload.email},
            )
        try:
            user = await self._repository.create(
                email=payload.email,
                name=payload.name,
                password_hash=hash_password(payload.password),
            )
        except ValueError as exc:
            # Lost a race against a concurrent register with the same email;
            # the repository's lock-protected check is authoritative.
            raise ConflictError(
                message="An account with this email already exists",
                details={"email": payload.email},
            ) from exc
        return self._start_session(user)

    async def login(self, payload: LoginRequest) -> AuthSession:
        """Verify credentials and start a session.

        Raises ``AuthenticationError`` for unknown email or wrong password
        (same message for both — no account enumeration).
        """
        user = await self._authenticate(payload.email, payload.password)
        return self._start_session(user)

    async def refresh(self, refresh_token: str | None) -> AuthSession:
        """Exchange a valid refresh token for a new session (rotation).

        Raises ``AuthenticationError`` if the token is missing, invalid,
        expired, or its user no longer exists.
        """
        if not refresh_token:
            raise AuthenticationError(message="Missing refresh token")
        payload = self._decode_refresh_token(refresh_token)
        if await self._is_revoked(payload.jti):
            raise AuthenticationError(message="Token has been revoked")
        user = await self._require_user(payload.user_id)
        return self._start_session(user)

    async def revoke(self, refresh_token: str | None) -> None:
        """Revoke a refresh token (logout).

        Invalid or already-used tokens are ignored — logout must never
        fail. Revocation is enforced by ``refresh`` via the denylist.
        """
        if not refresh_token:
            return
        try:
            payload = self._decode_refresh_token(refresh_token)
        except AuthenticationError:
            return  # already invalid — nothing to revoke
        self._denylist.revoke(payload.jti, expires_at=payload.expires_at)

    # -- internals -----------------------------------------------------

    async def _authenticate(self, email: str, password: str) -> User:
        """Return the user for valid credentials, else raise 401."""
        user = await self._repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError(message="Invalid email or password")
        return user

    def _decode_refresh_token(self, token: str):
        """Decode a refresh token or raise 401."""
        try:
            return decode_token(token, expected_type="refresh")
        except (jwt.PyJWTError, ValueError) as exc:
            raise AuthenticationError(
                message="Invalid or expired refresh token"
            ) from exc

    async def _is_revoked(self, jti: str) -> bool:
        """True if the token id is denylisted."""
        return self._denylist.is_revoked(jti)

    async def _require_user(self, user_id: UUID) -> User:
        """Load a user by id or raise 401."""
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError(message="User no longer exists")
        return user

    def _start_session(self, user: User) -> AuthSession:
        """Build tokens + a fresh rotating refresh token for a user."""
        return AuthSession(
            tokens=_build_tokens(user.id),
            refresh_token=create_refresh_token(user.id),
            user=user,
        )


def _build_tokens(user_id: UUID) -> TokenResponse:
    """Access-token response for a user."""
    return TokenResponse(
        access_token=create_access_token(user_id),
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )
