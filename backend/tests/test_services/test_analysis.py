"""Service tests for the roast pipeline (AI fully mocked)."""

from typing import Any
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
from app.models.user import TIER_DEMO
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    JobMatchEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)
from app.schemas.report import RoastReport
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
    "job_matcher": JobMatchEvaluatorOutput(
        summary="Strong backend fit.",
        match_rating="good",
        matched_skills=["Python", "PostgreSQL"],
        missing_skills=["Kubernetes operations"],
        recommendations=["Quantify API scale"],
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
    captured: dict[str, Any] | None = None,
) -> None:
    """Stub parse_resume / run_evaluations / compose_roast at the seams.

    ``captured`` (when given) receives the context and custom_instructions
    the pipeline handed to the seams — used to assert mode wiring.
    """

    async def fake_parse_resume(raw_text: str) -> StructuredResume:
        if fail_parsing is not None:
            raise RuntimeError(fail_parsing)
        return STRUCTURED

    async def fake_run_evaluations(
        resume_data: dict, mode: str, context: dict | None = None
    ) -> EvaluatorResults:
        if captured is not None:
            captured["mode"] = mode
            captured["context"] = context
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

    def _mock_report(roast_text: str) -> RoastReport:
        from app.schemas.report import MarketVerdict

        return RoastReport(
            headline_verdict="Generic resume, generic outcome.",
            verdict_summary="It will not survive a 2026 screening stack.",
            five_second_impression='"Pass — nothing verifiable here."',
            poison_points=["No quantified system-scale metrics."],
            market_analysis=[
                MarketVerdict(
                    market="Product Tech & Tier-1",
                    verdict="high rejection risk",
                    analysis="No scale, no ownership evidence.",
                    missing_signals=[],
                ),
                MarketVerdict(
                    market="Service & Consulting",
                    verdict="high rejection risk",
                    analysis="No client-ready signals.",
                    missing_signals=[],
                ),
                MarketVerdict(
                    market="2026 AI-Era Market",
                    verdict="high rejection risk",
                    analysis="No eval or cost metrics.",
                    missing_signals=[],
                ),
            ],
            roast=roast_text,
        )

    async def fake_compose_roast(aggregated, scoring, custom_instructions=None):
        if captured is not None:
            captured["custom_instructions"] = custom_instructions
        return _mock_report(roast), roast_fallback, _usage()

    monkeypatch.setattr(analysis_module, "parse_resume", fake_parse_resume)
    monkeypatch.setattr(analysis_module, "run_evaluations", fake_run_evaluations)
    monkeypatch.setattr(analysis_module, "compose_roast", fake_compose_roast)


async def _make_queued_analysis(
    db_session: AsyncSession,
    email_factory,
    *,
    raw_text: str | None = "Jane Doe resume",
    analysis_type: str = "general",
    target_role: str | None = None,
    job_description: str | None = None,
    custom_instructions: str | None = None,
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
        analysis_type=analysis_type,
        target_role=target_role,
        job_description=job_description,
        custom_instructions=custom_instructions,
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
        "job_matcher",
        "composer",
    }

    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None
    assert result.final_roast == "Your resume needs work, and here is why."
    reality = (result.final_report or {}).get("reality_check") or {}
    assert reality.get("headline_verdict")
    assert reality.get("five_second_impression")
    assert len(reality.get("market_analysis") or []) == 3
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
    assert usage_count == 6  # 5 evaluator outputs (incl. job_matcher mock) + 1 composer

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


async def test_role_based_pipeline_passes_context_and_persists_job_match(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    captured: dict[str, Any] = {}
    _patch_ai(monkeypatch, captured=captured)
    analysis = await _make_queued_analysis(
        db_session,
        email_factory,
        analysis_type="role_based",
        target_role="backend_dev",
    )

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "completed", analysis.error_message
    # The mode + context reached the orchestrator seam...
    assert captured["mode"] == "role_based"
    assert captured["context"]["target_role"] == "backend_dev"
    assert captured["context"]["role_slug"] == "backend_dev"
    # ...and the Job Matcher output was persisted on the result row.
    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None
    assert result.job_match_feedback is not None
    assert result.job_match_feedback["summary"] == "Strong backend fit."


async def test_custom_mode_passes_user_focus_to_composer(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    captured: dict[str, Any] = {}
    _patch_ai(monkeypatch, captured=captured)
    analysis = await _make_queued_analysis(
        db_session,
        email_factory,
        analysis_type="custom",
        custom_instructions="Tear apart my bullet points",
    )

    await _execute_pipeline(db_session, analysis.id)

    await db_session.refresh(analysis)
    assert analysis.status == "completed", analysis.error_message
    assert captured["mode"] == "custom"
    assert captured["custom_instructions"] == "Tear apart my bullet points"


async def test_create_analysis_rejects_incomplete_mode_context(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    """role_based needs target_role; jd_based needs job_description."""
    from app.common.exceptions import ValidationError

    _patch_ai(monkeypatch)
    service = AnalysisService(db_session)
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("modes"),
        name="Modes",
        password_hash="hash",
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/modes.docx",
        original_name="modes.docx",
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
            analysis_type="role_based",
            schedule=False,
        )

    with pytest.raises(ValidationError):
        await service.create_analysis(
            user_id=user.id,
            resume_id=resume.id,
            analysis_type="jd_based",
            schedule=False,
        )

    # With the required context both modes validate and queue.
    role_based = await service.create_analysis(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="role_based",
        target_role="backend_dev",
        schedule=False,
    )
    assert role_based.status == "queued"

    jd_based = await service.create_analysis(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="jd_based",
        job_description="Build APIs with Python. Own Postgres schemas.",
        schedule=False,
    )
    assert jd_based.status == "queued"


async def test_daily_cap_is_per_tier(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    """Pro users draw from rate_limit_pro, not the free cap."""
    from sqlalchemy import update

    from app.models.user import UserModel

    _patch_ai(monkeypatch)
    service = AnalysisService(db_session)
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("pro"),
        name="Pro User",
        password_hash="hash",
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/pro.docx",
        original_name="pro.docx",
        file_size=100,
        mime_type=DOCX_MIME,
        raw_text="some text",
    )
    db_session.add(resume)
    await db_session.flush()
    await db_session.execute(
        update(UserModel).where(UserModel.id == user.id).values(tier="pro")
    )
    await db_session.flush()

    monkeypatch.setattr(analysis_module.settings, "rate_limit_free", 0)
    monkeypatch.setattr(analysis_module.settings, "rate_limit_pro", 1)

    # A free user is capped at 0 — pro gets their own budget.
    from app.common.exceptions import RateLimitError

    assert user.id is not None
    with pytest.raises(RateLimitError):
        await service.create_analysis(
            user_id=user.id,
            resume_id=resume.id,
            tier="free",
            schedule=False,
        )

    first = await service.create_analysis(
        user_id=user.id, resume_id=resume.id, tier="pro", schedule=False
    )
    assert first.status == "queued"
    with pytest.raises(RateLimitError):
        await service.create_analysis(
            user_id=user.id, resume_id=resume.id, tier="pro", schedule=False
        )


async def test_usage_rows_carry_cost_when_pricing_is_configured(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    from decimal import Decimal

    _patch_ai(monkeypatch)
    monkeypatch.setattr(analysis_module.settings, "ai_input_price_per_m", 0.30)
    monkeypatch.setattr(analysis_module.settings, "ai_output_price_per_m", 2.50)
    analysis = await _make_queued_analysis(db_session, email_factory)

    await _execute_pipeline(db_session, analysis.id)

    usage_rows = (
        await db_session.scalars(
            select(AnalysisUsageModel).where(
                AnalysisUsageModel.analysis_id == analysis.id
            )
        )
    ).all()
    assert usage_rows
    # 100 prompt tokens at 0.30/1M + 50 completion tokens at 2.50/1M
    expected = Decimal(str(round(100 / 1_000_000 * 0.30 + 50 / 1_000_000 * 2.50, 6)))
    assert all(row.cost_usd == expected for row in usage_rows)


async def test_role_based_pipeline_uses_role_based_weights(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    captured: dict[str, Any] = {}
    _patch_ai(monkeypatch, captured=captured)
    analysis = await _make_queued_analysis(
        db_session,
        email_factory,
        analysis_type="role_based",
        target_role="backend_dev",
    )

    await _execute_pipeline(db_session, analysis.id)

    result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert result is not None
    stored = (result.scoring_methodology or {})["mode_weights"]
    assert stored["role_relevance"] == 0.25  # role_based table, not general's 0.15


async def test_demo_tier_bypasses_daily_cap(
    db_session: AsyncSession, email_factory, monkeypatch
) -> None:
    """The demo tier is the walkthrough baseline — uncapped even at limit 0."""
    _patch_ai(monkeypatch)
    service = AnalysisService(db_session)
    user = await PostgresUserRepository(db_session).create(
        email=email_factory("demo"),
        name="Demo User",
        password_hash="hash",
        tier=TIER_DEMO,
    )
    resume = ResumeModel(
        user_id=user.id,
        file_path=f"{user.id}/demo.docx",
        original_name="demo.docx",
        file_size=100,
        mime_type=DOCX_MIME,
        raw_text="some text",
    )
    db_session.add(resume)
    await db_session.flush()

    monkeypatch.setattr(analysis_module.settings, "rate_limit_free", 0)

    for _ in range(3):
        analysis = await service.create_analysis(
            user_id=user.id, resume_id=resume.id, tier=TIER_DEMO, schedule=False
        )
        assert analysis.status == "queued"
