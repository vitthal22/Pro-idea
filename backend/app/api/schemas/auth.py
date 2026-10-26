"""Pydantic schemas for the auth API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    name: str = Field(min_length=1, max_length=100, description="Display name")
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="Password")


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=1, description="Password")


class TokenResponse(BaseModel):
    """Access token response.

    The refresh token travels as an HttpOnly cookie, never in the body.
    """

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token lifetime in seconds")


class UserResponse(BaseModel):
    """Public user representation (no password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    tier: str
    created_at: datetime
