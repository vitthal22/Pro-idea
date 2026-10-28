"""create resumes, analyses, analysis_results, analysis_usage

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26

``prompt_versions`` is intentionally absent: ARCHITECTURE.md keeps prompt
versioning as file constants for the MVP (a table is a V2 concern).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the resume/analysis tables and their indexes."""
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("structured_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "parsing_status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("parsing_errors", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column("target_role", sa.String(length=100), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prompt_versions_used", postgresql.JSONB(), nullable=True),
        sa.Column("ai_model_used", sa.String(length=100), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analyses_user_id", "analyses", ["user_id"])
    op.create_index("idx_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("idx_analyses_status", "analyses", ["status"])
    op.create_index("idx_analyses_created_at", "analyses", ["created_at"])

    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recruiter_feedback", postgresql.JSONB(), nullable=True),
        sa.Column("ats_feedback", postgresql.JSONB(), nullable=True),
        sa.Column("technical_feedback", postgresql.JSONB(), nullable=True),
        sa.Column("content_feedback", postgresql.JSONB(), nullable=True),
        sa.Column("job_match_feedback", postgresql.JSONB(), nullable=True),
        sa.Column("critical_issues", postgresql.JSONB(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(), nullable=True),
        sa.Column("suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("positive_notes", postgresql.JSONB(), nullable=True),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scoring_breakdown", postgresql.JSONB(), nullable=True),
        sa.Column("scoring_methodology", postgresql.JSONB(), nullable=True),
        sa.Column("final_roast", sa.Text(), nullable=True),
        sa.Column("final_report", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_id",
            name="uq_analysis_results_analysis_id",
        ),
    )

    op.create_table(
        "analysis_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_model", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_usage_user_id", "analysis_usage", ["user_id"])


def downgrade() -> None:
    """Drop the analysis tables in dependency order."""
    op.drop_index("idx_usage_user_id", table_name="analysis_usage")
    op.drop_table("analysis_usage")
    op.drop_table("analysis_results")
    op.drop_index("idx_analyses_created_at", table_name="analyses")
    op.drop_index("idx_analyses_status", table_name="analyses")
    op.drop_index("idx_analyses_resume_id", table_name="analyses")
    op.drop_index("idx_analyses_user_id", table_name="analyses")
    op.drop_table("analyses")
    op.drop_index("idx_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")
