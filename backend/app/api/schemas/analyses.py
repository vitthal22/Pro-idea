"""Pydantic schemas for the analyses API."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisCreateRequest(BaseModel):
    """Request body for starting a roast."""

    resume_id: UUID = Field(description="Resume to analyze (must be yours)")
    analysis_type: Literal["general", "role_based", "jd_based", "custom"] = Field(
        "general", description="Only 'general' is wired in the MVP"
    )
    target_role: str | None = Field(None, max_length=100)
    job_description: str | None = Field(None, max_length=5000)
    custom_instructions: str | None = Field(None, max_length=500)


class AnalysisCreatedResponse(BaseModel):
    """Acknowledgement for an accepted analysis — poll or fetch later."""

    analysis_id: UUID
    status: str


class AnalysisListItemResponse(BaseModel):
    """One analysis in a history listing."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    analysis_type: str
    status: str
    created_at: datetime
    overall_score: float | None = None


class AnalysisListResponse(BaseModel):
    """A user's analyses, newest first."""

    items: list[AnalysisListItemResponse]
    total: int


class AnalysisStatusResponse(BaseModel):
    """Lightweight poll shape — status only, no heavy payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    error_message: str | None


class AnalysisResultPayload(BaseModel):
    """The roast itself: score, findings, breakdown, and the final text."""

    overall_score: float | None
    critical_issues: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    positive_notes: list[str]
    final_roast: str | None
    breakdown: dict[str, Any] | None = Field(
        description="Deterministic checks + AI category scores"
    )
    methodology: dict[str, Any] | None = Field(
        description="Weights, renormalization, partial-failure flags"
    )
    evaluator_summaries: dict[str, str]
    failed_evaluators: list[str]
    roast_fallback_used: bool = Field(
        description="True when the narrative roast used the deterministic template"
    )


class AnalysisDetailResponse(BaseModel):
    """Full analysis record including its result when finished."""

    id: UUID
    resume_id: UUID
    analysis_type: str
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    processing_time_ms: int | None
    result: AnalysisResultPayload | None
