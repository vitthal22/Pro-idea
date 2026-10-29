"""API tests for the analyses endpoints (background pipeline stubbed)."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import settings
from app.services import analysis as analysis_service_module

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
LONG_RESUME = " ".join(f"skill{i}" for i in range(130))
ANALYSES = "/api/v1/analyses"


@pytest.fixture
def scheduled_ids(monkeypatch: pytest.MonkeyPatch) -> Iterator[list]:
    """Stub the fire-and-forget scheduler; tests inspect what was scheduled."""
    ids: list = []
    monkeypatch.setattr(analysis_service_module, "schedule_pipeline", ids.append)
    yield ids


async def _upload_resume(
    client: AsyncClient, auth_headers: dict[str, str], docx_bytes_factory
) -> str:
    response = await client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume.docx", docx_bytes_factory(LONG_RESUME), DOCX_MIME)},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_create_analysis_returns_202_and_schedules_pipeline(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)

    response = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": resume_id, "analysis_type": "general"},
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert [str(item) for item in scheduled_ids] == [body["analysis_id"]]


async def test_create_analysis_unknown_resume_404(
    client, auth_headers, scheduled_ids
) -> None:
    response = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": str(uuid4()), "analysis_type": "general"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_create_analysis_unwired_mode_400(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)

    response = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": resume_id, "analysis_type": "jd_based"},
    )

    assert response.status_code == 400
    assert "not available" in response.json()["error"]["message"]


async def test_create_analysis_for_other_users_resume_404(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    # A second user uploads their own resume.
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Other User",
            "email": "other-analyses@example.com",
            "password": "Secret123",
        },
    )
    assert register.status_code == 201
    other_headers = {"Authorization": f"Bearer {register.json()['access_token']}"}
    other_resume_id = await _upload_resume(client, other_headers, docx_bytes_factory)

    response = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": other_resume_id, "analysis_type": "general"},
    )

    assert response.status_code == 404


async def test_create_analysis_unauthenticated_401(client, scheduled_ids) -> None:
    response = await client.post(
        ANALYSES, json={"resume_id": str(uuid4()), "analysis_type": "general"}
    )

    assert response.status_code == 401


async def test_list_analyses_shows_created_analysis(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)
    created = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": resume_id, "analysis_type": "general"},
    )

    response = await client.get(ANALYSES, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == created.json()["analysis_id"]
    assert body["items"][0]["status"] == "queued"
    assert body["items"][0]["overall_score"] is None


async def test_get_status_and_detail_while_queued(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)
    created = (
        await client.post(
            ANALYSES,
            headers=auth_headers,
            json={"resume_id": resume_id, "analysis_type": "general"},
        )
    ).json()

    status_response = await client.get(
        f"{ANALYSES}/{created['analysis_id']}/status", headers=auth_headers
    )
    detail_response = await client.get(
        f"{ANALYSES}/{created['analysis_id']}", headers=auth_headers
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["resume_id"] == resume_id
    assert detail["result"] is None


async def test_other_user_cannot_read_analysis(
    client, auth_headers, docx_bytes_factory, scheduled_ids
) -> None:
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)
    created = (
        await client.post(
            ANALYSES,
            headers=auth_headers,
            json={"resume_id": resume_id, "analysis_type": "general"},
        )
    ).json()

    stranger = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Stranger",
            "email": "stranger-analyses@example.com",
            "password": "Secret123",
        },
    )
    stranger_headers = {"Authorization": f"Bearer {stranger.json()['access_token']}"}

    for path in (
        f"{ANALYSES}/{created['analysis_id']}",
        f"{ANALYSES}/{created['analysis_id']}/status",
    ):
        response = await client.get(path, headers=stranger_headers)
        assert response.status_code == 404


async def test_daily_rate_limit_returns_429(
    client, auth_headers, docx_bytes_factory, scheduled_ids, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "rate_limit_free", 1)
    resume_id = await _upload_resume(client, auth_headers, docx_bytes_factory)

    first = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": resume_id, "analysis_type": "general"},
    )
    second = await client.post(
        ANALYSES,
        headers=auth_headers,
        json={"resume_id": resume_id, "analysis_type": "general"},
    )

    assert first.status_code == 202
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMITED"
