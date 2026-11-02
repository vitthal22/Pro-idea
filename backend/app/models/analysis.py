"""SQLAlchemy models for ``analyses`` and ``analysis_results``.

Storage only. Feedback columns are JSONB so evaluator schemas can evolve
without a migration; ``analysis_results`` holds the denormalized snapshot
the API reads.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.resume import ResumeModel
    from app.models.user import UserModel


class AnalysisModel(Base):
    """A single analysis request and its lifecycle status."""

    __tablename__ = "analyses"
    __table_args__ = (
        Index("idx_analyses_user_id", "user_id"),
        Index("idx_analyses_resume_id", "resume_id"),
        Index("idx_analyses_status", "status"),
        Index("idx_analyses_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(100))
    job_description: Mapped[str | None] = mapped_column(Text)
    custom_instructions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    prompt_versions_used: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    ai_model_used: Mapped[str | None] = mapped_column(String(100))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserModel"] = relationship(
        back_populates="analyses",
        lazy="raise",
    )
    resume: Mapped["ResumeModel"] = relationship(
        back_populates="analyses",
        lazy="raise",
    )
    result: Mapped["AnalysisResultModel | None"] = relationship(
        back_populates="analysis",
        lazy="raise",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AnalysisResultModel(Base):
    """Denormalized output of one analysis (one row per analysis)."""

    __tablename__ = "analysis_results"
    __table_args__ = (
        UniqueConstraint("analysis_id", name="uq_analysis_results_analysis_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    recruiter_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ats_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    technical_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    content_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    job_match_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    critical_issues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    warnings: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    suggestions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    positive_notes: Mapped[list[str] | None] = mapped_column(JSONB)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    scoring_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    scoring_methodology: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    final_roast: Mapped[str | None] = mapped_column(Text)
    final_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis: Mapped["AnalysisModel"] = relationship(
        back_populates="result",
        lazy="raise",
    )
