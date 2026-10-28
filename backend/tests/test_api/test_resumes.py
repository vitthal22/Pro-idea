"""Resume API tests: upload, listing, ownership, deletion, failures."""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.resume import ResumeModel
from app.storage.local_storage import LocalStorage

LONG_RESUME = " ".join(f"skill{i}" for i in range(130))
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
UPLOAD = "/api/v1/resumes/upload"
LIST = "/api/v1/resumes"


async def _upload_docx(
    client,
    auth_headers: dict[str, str],
    docx_bytes_factory,
    body: str = LONG_RESUME,
):
    return await client.post(
        UPLOAD,
        headers=auth_headers,
        files={"file": ("resume.docx", docx_bytes_factory(body), DOCX_MIME)},
    )


async def test_upload_docx_extracts_text(
    client,
    auth_headers,
    docx_bytes_factory,
    db_session: AsyncSession,
    test_storage: LocalStorage,
) -> None:
    response = await _upload_docx(client, auth_headers, docx_bytes_factory)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["parsing_status"] == "completed"
    assert body["original_name"] == "resume.docx"
    assert body["mime_type"] == DOCX_MIME
    assert body["raw_text"]
    assert body["parsing_errors"] is None
    assert body["structured_data"]["extraction_method"] == "extract_docx"
    assert body["structured_data"]["truncated"] is False

    resume = await db_session.scalar(
        select(ResumeModel).where(ResumeModel.id == body["id"])
    )
    assert resume is not None
    assert test_storage.get_path(resume.file_path).exists()


async def test_upload_pdf_extracts_text(
    client,
    auth_headers,
    pdf_bytes_factory,
) -> None:
    response = await client.post(
        UPLOAD,
        headers=auth_headers,
        files={
            "file": (
                "cv.pdf",
                pdf_bytes_factory(f"Staff engineer {LONG_RESUME}"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["structured_data"]["extraction_method"] == "extract_pdf"
    assert "Staff engineer" in body["raw_text"]


async def test_list_and_get_resume(
    client,
    auth_headers,
    docx_bytes_factory,
) -> None:
    uploaded = (await _upload_docx(client, auth_headers, docx_bytes_factory)).json()

    listing = await client.get(LIST, headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == uploaded["id"]
    assert "raw_text" not in listing.json()["items"][0]

    detail = await client.get(f"{LIST}/{uploaded['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == uploaded["id"]
    assert detail.json()["raw_text"]


async def test_delete_resume_removes_file_and_record(
    client,
    auth_headers,
    docx_bytes_factory,
    db_session: AsyncSession,
    test_storage: LocalStorage,
) -> None:
    resume_id = (await _upload_docx(client, auth_headers, docx_bytes_factory)).json()[
        "id"
    ]
    resume = await db_session.scalar(
        select(ResumeModel).where(ResumeModel.id == resume_id)
    )
    assert resume is not None
    path = test_storage.get_path(resume.file_path)
    assert path.exists()

    response = await client.delete(f"{LIST}/{resume_id}", headers=auth_headers)

    assert response.status_code == 204
    assert not path.exists()
    after = await client.get(f"{LIST}/{resume_id}", headers=auth_headers)
    assert after.status_code == 404
    listing = await client.get(LIST, headers=auth_headers)
    assert listing.json()["total"] == 0


async def test_other_user_cannot_read_or_delete(
    client,
    auth_headers,
    docx_bytes_factory,
) -> None:
    resume_id = (await _upload_docx(client, auth_headers, docx_bytes_factory)).json()[
        "id"
    ]
    stranger = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Stranger",
            "email": f"stranger-{uuid4().hex[:12]}@example.com",
            "password": "Secret123",
        },
    )
    stranger_headers = {"Authorization": f"Bearer {stranger.json()['access_token']}"}

    assert (
        await client.get(f"{LIST}/{resume_id}", headers=stranger_headers)
    ).status_code == 404
    assert (
        await client.delete(f"{LIST}/{resume_id}", headers=stranger_headers)
    ).status_code == 404
    assert (
        await client.get(f"{LIST}/{resume_id}", headers=auth_headers)
    ).status_code == 200


async def test_upload_requires_authentication(client, docx_bytes_factory) -> None:
    response = await client.post(
        UPLOAD,
        files={"file": ("resume.docx", docx_bytes_factory(LONG_RESUME), DOCX_MIME)},
    )

    assert response.status_code == 401


async def test_rejects_unsupported_file_type(
    client,
    auth_headers,
) -> None:
    response = await client.post(
        UPLOAD,
        headers=auth_headers,
        files={"file": ("notes.txt", b"just some text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE"


async def test_rejects_empty_file(client, auth_headers) -> None:
    response = await client.post(
        UPLOAD,
        headers=auth_headers,
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE"


async def test_rejects_oversized_file(
    client,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "max_file_size_mb", 1)
    oversized = b"%PDF-1.4\n" + b"A" * (1024 * 1024 + 10)

    response = await client.post(
        UPLOAD,
        headers=auth_headers,
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )

    assert response.status_code == 400
    assert "limit" in response.json()["error"]["message"]


async def test_low_quality_upload_is_recorded_as_failed(
    client,
    auth_headers,
    docx_bytes_factory,
    db_session: AsyncSession,
) -> None:
    response = await _upload_docx(
        client,
        auth_headers,
        docx_bytes_factory,
        body="too short",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PARSING_FAILED"

    resume = await db_session.scalar(select(ResumeModel))
    assert resume is not None
    assert resume.parsing_status == "failed"
    assert resume.raw_text is None
    assert resume.parsing_errors is not None
    assert resume.parsing_errors[0]["code"] == "PARSING_FAILED"


@pytest.mark.parametrize("header_value", ["Bearer garbage", "garbage"])
async def test_invalid_token_rejected(client, header_value: str) -> None:
    response = await client.get(LIST, headers={"Authorization": header_value})

    assert response.status_code == 401
