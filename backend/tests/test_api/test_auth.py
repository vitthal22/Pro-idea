"""Auth API tests: status codes, cookies, and error bodies."""

from typing import Any

from httpx import AsyncClient

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"
PASSWORD = "Secret123"
INVALID_CREDENTIALS = "Invalid email or password"


async def _register(client: AsyncClient, email: str) -> dict[str, Any]:
    response = await client.post(
        REGISTER,
        json={"name": "API User", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_register_returns_access_token_and_refresh_cookie(
    client: AsyncClient,
    email_factory,
) -> None:
    body = await _register(client, email_factory("api"))

    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"]
    assert "refresh_token" not in body

    cookie = client.cookies.get("refresh_token")
    assert cookie is not None


async def test_refresh_cookie_flags_are_hardened(
    client: AsyncClient,
    email_factory,
) -> None:
    response = await client.post(
        REGISTER,
        json={
            "name": "Cookie Test",
            "email": email_factory("cookie"),
            "password": PASSWORD,
        },
    )

    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "path=/api/v1/auth" in set_cookie
    assert "samesite=lax" in set_cookie


async def test_duplicate_register_returns_409(
    client: AsyncClient,
    email_factory,
) -> None:
    email = email_factory("dup")
    await _register(client, email)

    response = await client.post(
        REGISTER,
        json={"name": "Again", "email": email, "password": PASSWORD},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_login_returns_token(
    client: AsyncClient,
    email_factory,
) -> None:
    email = email_factory("login")
    await _register(client, email)

    response = await client.post(LOGIN, json={"email": email, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_login_wrong_password_returns_401(
    client: AsyncClient,
    email_factory,
) -> None:
    email = email_factory("badpw")
    await _register(client, email)

    response = await client.post(
        LOGIN,
        json={"email": email, "password": "WrongPass123"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == INVALID_CREDENTIALS


async def test_login_unknown_email_returns_same_message(
    client: AsyncClient,
    email_factory,
) -> None:
    response = await client.post(
        LOGIN,
        json={"email": email_factory("ghost"), "password": PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == INVALID_CREDENTIALS


async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get(ME)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_me_returns_profile_for_token(
    client: AsyncClient,
    email_factory,
) -> None:
    email = email_factory("me")
    body = await _register(client, email)

    response = await client.get(
        ME,
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == email
    assert profile["tier"] == "free"
    assert "password_hash" not in profile


async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get(ME, headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401


async def test_refresh_rotates_the_cookie(
    client: AsyncClient,
    email_factory,
) -> None:
    await _register(client, email_factory("rotate"))
    first_cookie = client.cookies.get("refresh_token")

    response = await client.post(REFRESH)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert client.cookies.get("refresh_token") not in (None, first_cookie)


async def test_refresh_without_cookie_returns_401(client: AsyncClient) -> None:
    response = await client.post(REFRESH)

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Missing refresh token"


async def test_logout_revokes_the_refresh_token(
    client: AsyncClient,
    email_factory,
) -> None:
    await _register(client, email_factory("logout"))
    stolen_token = client.cookies.get("refresh_token")
    assert stolen_token is not None

    logout = await client.post(LOGOUT)

    assert logout.status_code == 204
    assert client.cookies.get("refresh_token") is None

    replay = await client.post(
        REFRESH,
        headers={"Cookie": f"refresh_token={stolen_token}"},
    )

    assert replay.status_code == 401
    assert replay.json()["error"]["message"] == "Token has been revoked"
