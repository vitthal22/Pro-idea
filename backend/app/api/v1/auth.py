"""Auth API endpoints.

Routers are HTTP-only: parse request, call service, shape response.
Cookies are set/cleared here (HTTP concern), never in the service layer.
"""

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import (
    clear_refresh_cookie,
    get_auth_service,
    get_current_user,
    get_refresh_token,
    set_refresh_cookie,
)
from app.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService
from app.services.user_repository import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
async def register(
    payload: RegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Create an account, start a session, and return the access token."""
    session = await auth_service.register(payload)
    set_refresh_cookie(response, session.refresh_token)
    return session.tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Verify credentials and return the access token (refresh cookie set)."""
    session = await auth_service.login(payload)
    set_refresh_cookie(response, session.refresh_token)
    return session.tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: str | None = Depends(get_refresh_token),
) -> TokenResponse:
    """Exchange the refresh cookie for a new access token (rotates cookie)."""
    session = await auth_service.refresh(refresh_token)
    set_refresh_cookie(response, session.refresh_token)
    return session.tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: str | None = Depends(get_refresh_token),
) -> None:
    """Invalidate the refresh token and clear the cookie."""
    await auth_service.revoke(refresh_token)
    clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
