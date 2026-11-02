"""Middleware tests: CORS assertions (M1.6) and request timing."""

from httpx import AsyncClient

from app.config import settings


async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    origin = settings.cors_origin_list[0]

    response = await client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_cors_preflight_allowed(client: AsyncClient) -> None:
    origin = settings.cors_origin_list[0]

    response = await client.options(
        "/api/v1/analyses",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]


async def test_cors_rejects_unknown_origin(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"Origin": "https://evil.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


async def test_requests_carry_process_time_header(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    float(response.headers["x-process-time"])
