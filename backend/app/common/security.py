"""JWT helpers.

All secrets, algorithms, and expiry values come from Settings — never
hardcoded — so environments differ only in their `.env` values.

Every token carries a ``jti`` (unique ID) so logout can denylist it.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings

_password_hasher = PasswordHash([BcryptHasher()])

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class TokenPayload:
    """The claims the app cares about, decoded from a JWT."""

    user_id: UUID
    jti: str
    expires_at: datetime


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _password_hasher.verify(password, password_hash)


def _create_token(
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: UUID) -> str:
    """Create a short-lived access token."""
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.jwt_expire_minutes),
    )


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived refresh token."""
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=settings.jwt_refresh_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    """Decode and validate a JWT.

    Raises ``jwt.PyJWTError`` for expired/invalid tokens and
    ``ValueError`` for a wrong token type.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != expected_type:
        raise ValueError(f"Expected {expected_type} token, got {payload.get('type')}")
    return TokenPayload(
        user_id=UUID(payload["sub"]),
        jti=str(payload["jti"]),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )
