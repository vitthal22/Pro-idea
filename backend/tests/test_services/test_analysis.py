"""Service tests for the roast pipeline (AI fully mocked)."""

from uuid import uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import EvaluatorResults
from app.ai.provider import AIResult
from app.models.analysis import AnalysisModel, AnalysisResultModel
from app.models.analysis_usage import AnalysisUsageModel
from app.models.resume import ResumeModel
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)
from app.schemas.resume import StructuredResume
from app.services import analysis as analysis_module
from app.services.analysis import AnalysisService, _execute_pipeline
from app.services.user_repository import PostgresUserRepository

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

STRUCTURED = StructuredResume.model_validate(
    {
        "contact_info": {"name": "Jane Doe", "email": "jane@example.com"},
        "experience": [
            {
                "job_title": "Backend Developer",
                "company": "Acme",
                "start_date": "Jan 2022",
                "bullet_points": ["Built APIs", "Cut latency 40%"],
            }
        ],
        "skills": ["Python", "FastAPI"],
    }
)

_EVALUATOR_PAYLOADS: dict[str, BaseModel] = {
    "recruiter": RecruiterEvaluatorOutput(
        summary="Solid.",
        first_impression="average",
        first_impression_reason="Generic opener.",
        experience_relevance_rating="good",
        credibility_rating="high",
        would_shortlist=True,
        would_shortlist_reason="Relevant experience",
    ),
    "ats": ATSEvaluatorOutput(summary="Parseable.", ats_readiness_rating="good"),
    "technical": TechnicalEvaluatorOutput(
        summary="Evidenced.", technical_depth_rating="good"
    ),
    "content_quality": ContentQualityEvaluatorOutput(
        summary="Decent.", writing_quality_rating="fair", quantification_rating="poor"
    ),
}


def _usage(model: str = "gemini/gemini-3.5-flash") -> AIResult:
    return AIResult(content="ok", model=model, prompt_tokens=100, completion_tokens=50)


def _patch_ai(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fail_parsing: str | None = None,
    failed_evaluators: dict[str, str] | None = None,
    roast: str = "Your resume needs work, and here is why.",
    roast_fallback: bool = False,
) -> None:
    """Stub parse_resume / run_evaluations / compose_roast at the seams."""

    async def fake_parse_resume(raw_text: str) -> StructuredResume:
        if fail_parsing is not None:
            raise RuntimeError(fail_parsing)
        return STRUCTURED

    async def fake_run_evaluations(resume_data: dict, mode: str) -> EvaluatorResults:
        outputs = {
            name: payload
            for name, payload in _EVALUATOR_PAYLOADS.items()
            if not failed_evaluators or name not in failed_evaluators
        }
        return EvaluatorResults(
            outputs=outputs,
            failed=failed_evaluators or {},
            usage=[_usage() for _ in outputs],
        )

    async def fake_compose_roast(aggregated, scoring):
        return roast, roast_fallback, _usage()

    monkeypatch.setattr(analysis_module, "parse_resume", fake_parse_resume)
    monkeypatch.setattr(analysis_module, "run_evaluations", fake_run_evaluations)
    monkeypatch.setattr(analysis_module, "compose_roast", fake_compose_roast)


async def _make_queued_analysis(
    db_session: AsyncSession, email_factory, *, raw_text: str | None = "Jane Doe resume"
) -> AnalysisModel:
    """A user + resume + queued analysis, all inside the test transaction."""
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("pipeline"),
        name="Pipeline User",
        password_hash="hash",
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/pipeline-test.docx",
        original_name="pipeline-test.docx",
        file_size=1234,
        mime_type=DOCX_MIME,
        raw_text=raw_text,
    )
    db_session.add(resume)
    await db_session.flush()
    analysis = AnalysisModel(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="general",
        status="queued",
    )
    db_session.add(analysis)
    await db_session.flush()
    return analysis


async def test_pipeline_success_persists_result_and_usage(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    _patch_ai(monkeypatch)
    analysis = await _make_queued_analysis(db_session, email_factory)

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "completed", analysis.error_message
    assert analysis.error_message is None
    assert analysis.processing_time_ms is not None
    assert analysis.ai_model_used == "gemini/gemini-3.5-flash"
    assert analysis.prompt_versions_used is not None
    assert set(analysis.prompt_versions_used) == {
        "parser",
        "recruiter",
        "ats",
        "technical",
        "content_quality",
        "composer",
    }

    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None
    assert result.final_roast == "Your resume needs work, and here is why."
    assert result.overall_score is not None
    assert result.recruiter_feedback is not None
    assert result.critical_issues is not None
    assert result.scoring_methodology is not None
    assert result.scoring_methodology["ai_partial"] is False

    usage_count = await db_session.scalar(
        select(func.count())
        .select_from(AnalysisUsageModel)
        .where(AnalysisUsageModel.analysis_id == analysis.id)
    )
    assert usage_count == 5  # 4 evaluators + 1 composer

    # Parsed data is stored back on the resume for reuse.
    stored_resume = await db_session.get(ResumeModel, analysis.resume_id)
    assert stored_resume is not None
    assert "parsed" in (stored_resume.structured_data or {})


async def test_pipeline_partial_when_an_evaluator_fails(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    _patch_ai(monkeypatch, failed_evaluators={"technical": "simulated outage"})
    analysis = await _make_queued_analysis(db_session, email_factory)

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "partial"
    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None  # degraded result is still stored
    assert result.technical_feedback is None
    assert result.scoring_methodology is not None
    assert result.scoring_methodology["failed_evaluators"] == ["technical"]
    assert result.final_report is not None
    assert result.final_report["failed_evaluators"] == ["technical"]


async def test_pipeline_failed_when_parsing_fails(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    _patch_ai(monkeypatch, fail_parsing="model returned garbage")
    analysis = await _make_queued_analysis(db_session, email_factory)

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "failed"
    assert analysis.error_message is not None
    assert "model returned garbage" in analysis.error_message
    assert analysis.completed_at is not None
    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is None


async def test_pipeline_failed_when_resume_has_no_text(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    _patch_ai(monkeypatch)
    analysis = await _make_queued_analysis(db_session, email_factory, raw_text=None)

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "failed"
    assert analysis.error_message is not None
    assert "no extracted text" in analysis.error_message


async def test_pipeline_marks_roast_fallback_as_partial(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    _patch_ai(monkeypatch, roast_fallback=True)
    analysis = await _make_queued_analysis(db_session, email_factory)

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "partial"


async def test_create_analysis_validates_ownership_mode_and_cap(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    from app.common.exceptions import NotFoundError, RateLimitError, ValidationError

    _patch_ai(monkeypatch)
    service = AnalysisService(db_session)
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("owner"),
        name="Owner",
        password_hash="hash",
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/own.docx",
        original_name="own.docx",
        file_size=100,
        mime_type=DOCX_MIME,
        raw_text="some text",
    )
    db_session.add(resume)
    await db_session.flush()

    with pytest.raises(ValidationError):
        await service.create_analysis(
            user_id=user.id,
            resume_id=resume.id,
            analysis_type="jd_based",
            schedule=False,
        )

    with pytest.raises(NotFoundError):
        await service.create_analysis(
            user_id=user.id, resume_id=uuid4(), schedule=False
        )

    monkeypatch.setattr(analysis_module.settings, "rate_limit_free", 1)
    first = await service.create_analysis(
        user_id=user.id, resume_id=resume.id, schedule=False
    )
    assert first.status == "queued"
    with pytest.raises(RateLimitError):
        await service.create_analysis(
            user_id=user.id, resume_id=resume.id, schedule=False
        )
