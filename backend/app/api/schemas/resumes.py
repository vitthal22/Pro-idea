"""Pydantic schemas for the resumes API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeResponse(BaseModel):
    """Resume summary used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    file_size: int = Field(description="Size in bytes")
    mime_type: str
    parsing_status: str
    created_at: datetime


class ResumeDetailResponse(ResumeResponse):
    """Single resume including the extracted text."""

    raw_text: str | None
    parsing_errors: list[dict[str, Any]] | None
    structured_data: dict[str, Any] | None


class ResumeListResponse(BaseModel):
    """A user's resumes."""

    items: list[ResumeResponse]
    total: int
