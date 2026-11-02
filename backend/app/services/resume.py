"""Resume business logic: upload, extraction, listing, soft delete.

Extraction is synchronous third-party parsing, so it runs in a worker
thread — never inline on the event loop.
"""

import asyncio
import io
import zipfile
from datetime import UTC, datetime
from uuid import UUID

import magic
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    InvalidFileError,
    NotFoundError,
    ResumeParsingError,
)
from app.document_processing.extractor import (
    DOCX_MIME_TYPE,
    PDF_MIME_TYPE,
    extract_text,
)
from app.models.resume import ResumeModel
from app.storage.base import Storage

ALLOWED_MIME_TYPES = frozenset({PDF_MIME_TYPE, DOCX_MIME_TYPE})
MAX_RAW_TEXT_CHARS = 50_000
READ_CHUNK_SIZE = 64 * 1024
SNIFF_BYTES = 2048
# Some libmagic builds label OOXML files as generic containers.
OPAQUE_MIME_TYPES = frozenset({"application/octet-stream", "application/zip"})
DOCX_DOCUMENT_PART = "word/document.xml"


class ResumeService:
    """Use cases for a user's resumes."""

    def __init__(
        self,
        session: AsyncSession,
        storage: Storage,
        max_file_size_mb: int,
    ) -> None:
        self._session = session
        self._storage = storage
        self._max_file_size_bytes = max_file_size_mb * 1024 * 1024

    async def upload(self, *, user_id: UUID, upload: UploadFile) -> ResumeModel:
        """Store the file, extract its text, and persist the record.

        Raises ``InvalidFileError`` for empty/oversized/unsupported files and
        ``ResumeParsingError`` when text cannot be extracted — in that case
        the record is kept with ``parsing_status="failed`` and FastAPI returns 422.
        """
        content = await self._read_within_limit(upload)
        mime_type = self._detect_mime_type(content)

        key = await self._storage.save(
            user_id=user_id,
            filename=upload.filename or "",
            content=content,
        )
        resume = ResumeModel(
            user_id=user_id,
            file_path=key,
            original_name=upload.filename or "resume",
            file_size=len(content),
            mime_type=mime_type,
            parsing_status="pending",
        )
        self._session.add(resume)
        await self._session.commit()
        await self._session.refresh(resume)

        try:
            await self._extract_into(resume)
        except ResumeParsingError as exc:
            resume.parsing_status = "failed"
            resume.parsing_errors = [
                {"code": exc.code, "message": exc.message, **exc.details}
            ]
            await self._session.commit()
            raise

        return resume

    async def get(self, *, user_id: UUID, resume_id: UUID) -> ResumeModel:
        """Return one resume owned by the user, else raise 404."""
        resume = await self._session.get(ResumeModel, resume_id)
        if resume is None or resume.user_id != user_id or resume.deleted_at is not None:
            raise NotFoundError(message="Resume not found")
        return resume

    async def list(self, *, user_id: UUID) -> list[ResumeModel]:
        """List the user's live resumes, newest first."""
        result = await self._session.execute(
            select(ResumeModel)
            .where(
                ResumeModel.user_id == user_id,
                ResumeModel.deleted_at.is_(None),
            )
            .order_by(ResumeModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, *, user_id: UUID, resume_id: UUID) -> None:
        """Remove the file and soft-delete the record."""
        resume = await self.get(user_id=user_id, resume_id=resume_id)
        await self._storage.delete(resume.file_path)
        resume.deleted_at = datetime.now(UTC)
        await self._session.commit()

    async def _extract_into(self, resume: ResumeModel) -> None:
        """Extract text off-loop and update the record."""
        try:
            extracted = await asyncio.to_thread(
                extract_text,
                self._storage.get_path(resume.file_path),
                resume.mime_type,
            )
        except ResumeParsingError as exc:
            resume.parsing_status = "failed"
            resume.parsing_errors = [
                {"code": exc.code, "message": exc.message, **exc.details}
            ]
            await self._session.flush()
            raise

        truncated = len(extracted.raw_text) > MAX_RAW_TEXT_CHARS
        resume.raw_text = extracted.raw_text[:MAX_RAW_TEXT_CHARS]
        resume.parsing_status = "completed"
        resume.parsing_errors = None
        resume.structured_data = {
            "extraction_method": extracted.extraction_method,
            "word_count": extracted.quality.word_count,
            "printable_ratio": round(extracted.quality.printable_ratio, 3),
            "truncated": truncated,
        }
        await self._session.commit()
        await self._session.refresh(resume)

    async def _read_within_limit(self, upload: UploadFile) -> bytes:
        """Read the upload in chunks, refusing anything over the size cap."""
        chunks: list[bytes] = []
        size = 0
        while chunk := await upload.read(READ_CHUNK_SIZE):
            size += len(chunk)
            if size > self._max_file_size_bytes:
                raise InvalidFileError(
                    message=(
                        f"File exceeds the "
                        f"{self._max_file_size_bytes // (1024 * 1024)} MB limit"
                    ),
                    details={
                        "max_file_size_mb": self._max_file_size_bytes // (1024 * 1024)
                    },
                )
            chunks.append(chunk)
        if not chunks:
            raise InvalidFileError(message="Uploaded file is empty")
        return b"".join(chunks)

    @classmethod
    def _detect_mime_type(cls, content: bytes) -> str:
        """Detect the real MIME type from the bytes, not the client header."""
        detected = magic.from_buffer(content[:SNIFF_BYTES], mime=True)
        if detected in ALLOWED_MIME_TYPES:
            return detected
        if detected in OPAQUE_MIME_TYPES and cls._is_docx_archive(content):
            return DOCX_MIME_TYPE
        raise InvalidFileError(
            message="Only PDF and DOCX files are supported",
            details={"detected_mime_type": detected},
        )

    @staticmethod
    def _is_docx_archive(content: bytes) -> bool:
        """True for a ZIP that really contains a Word document part."""
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                return DOCX_DOCUMENT_PART in archive.namelist()
        except (zipfile.BadZipFile, OSError):
            return False
