"""Integration test: the full roast pipeline against the real AI provider.

Opt-in (it makes real API calls and takes ~2-4 minutes):

    RUN_INTEGRATION=1 npm test --prefix backend
    # or: RUN_INTEGRATION=1 .venv/Scripts/python.exe -m pytest -m integration

Skipped unless RUN_INTEGRATION=1 **and** a GEMINI_API_KEY is configured.
Uses the transaction-rollback fixtures, so nothing persists.
"""

import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisResultModel
from app.models.analysis_usage import AnalysisUsageModel
from app.services.analysis import AnalysisService
from app.services.user_repository import PostgresUserRepository

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION") != "1",
        reason="set RUN_INTEGRATION=1 to run real-AI integration tests",
    ),
    pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not configured",
    ),
]

LONG_RESUME = (
    "Vitthal Gupta — Backend developer with five years of experience "
    "building reliable web applications, distributed systems, and public "
    "APIs for growing product teams. "
    "Software Engineer, Acme Corp, 2022-Present. Designed and built REST "
    "APIs with FastAPI serving two million requests per day across multiple "
    "regional deployments. Reduced database latency by forty percent through "
    "query optimization, connection pooling, and strategic indexing. "
    "Mentored three junior engineers through weekly code reviews and "
    "architecture discussions. "
    "Junior Developer, Beta LLC, 2021-2022. Implemented customer dashboards "
    "in React and TypeScript with automated end-to-end testing. "
    "Skills: Python, FastAPI, PostgreSQL, Docker, Redis, React, TypeScript, "
    "Kubernetes. "
    "B.Tech in Computer Science, State University, 2021."
)


@pytest.mark.timeout(600)
async def test_full_pipeline_against_real_ai(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    """Upload → parse → evaluate → score → compose, with real Gemini calls."""
    from app.models.resume import ResumeModel

    service = AnalysisService(db_session)
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("integration"),
        name="Integration User",
        password_hash="hash",
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/integration.docx",
        original_name="integration.docx",
        file_size=len(LONG_RESUME) * 8,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        raw_text=LONG_RESUME,
    )
    db_session.add(resume)
    await db_session.flush()

    analysis = await service.create_analysis(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="general",
        schedule=False,
    )

    from app.services.analysis import _execute_pipeline

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status in ("completed", "partial"), analysis.error_message
    assert analysis.processing_time_ms is not None
    assert analysis.ai_model_used, "the primary model should be recorded"

    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None
    assert result.overall_score is not None and 0 <= result.overall_score <= 100
    assert result.final_roast and len(result.final_roast.split()) >= 80
    assert result.recruiter_feedback is not None

    usage_rows = (
        await db_session.scalars(
            select(AnalysisUsageModel).where(
                AnalysisUsageModel.analysis_id == analysis.id
            )
        )
    ).all()
    assert len(usage_rows) >= 5  # 4 evaluators + composer
    assert all(row.prompt_tokens and row.completion_tokens for row in usage_rows)
