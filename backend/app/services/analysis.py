"""Analysis service — create analyses and run the roast pipeline.

``create_analysis`` validates ownership/mode/rate-limit, inserts a row with
status ``queued``, and schedules the pipeline as a fire-and-forget task.
The pipeline runs in its **own** database session (never the request's), so
a client disconnect or timeout never loses the work — the durable state is
the ``analyses``/``analysis_results`` rows, polled via the status endpoint.

Status flow (single source of truth, ARCHITECTURE §11):
``queued → extracting → parsing → evaluating → scoring → composing →
completed | partial | failed``.
``partial`` means at least one evaluator failed or the roast fell back to
the deterministic template — the result is still stored and served.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.aggregator import aggregate_results
from app.ai.composer import compose_roast
from app.ai.orchestrator import get_evaluators_for_mode, run_evaluations
from app.ai.parser import parse_resume
from app.ai.prompts.composer import VERSION as COMPOSER_VERSION
from app.ai.prompts.evaluators.ats import VERSION as ATS_VERSION
from app.ai.prompts.evaluators.content_quality import VERSION as CONTENT_VERSION
from app.ai.prompts.evaluators.job_matcher import VERSION as JOB_MATCHER_VERSION
from app.ai.prompts.evaluators.recruiter import VERSION as RECRUITER_VERSION
from app.ai.prompts.evaluators.technical import VERSION as TECHNICAL_VERSION
from app.ai.prompts.parser import VERSION as PARSER_VERSION
from app.ai.prompts.roles import get_role_context
from app.ai.scoring import calculate_scores
from app.common.exceptions import (
    AnalysisFailedError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.config import settings
from app.db.session import get_session_factory
from app.models.analysis import AnalysisModel, AnalysisResultModel
from app.models.analysis_usage import AnalysisUsageModel
from app.models.resume import ResumeModel

logger = logging.getLogger("app.services.analysis")

# Every prompt the pipeline may load, recorded on the analysis row so any
# result is reproducible against its exact prompt versions.
PROMPT_VERSIONS: dict[str, str] = {
    "parser": PARSER_VERSION,
    "recruiter": RECRUITER_VERSION,
    "ats": ATS_VERSION,
    "technical": TECHNICAL_VERSION,
    "content_quality": CONTENT_VERSION,
    "job_matcher": JOB_MATCHER_VERSION,
    "composer": COMPOSER_VERSION,
}


def _tier_daily_limit(tier: str) -> int:
    """Per-tier daily analysis cap from settings (free default)."""
    return settings.rate_limit_pro if tier == "pro" else settings.rate_limit_free


async def _enforce_daily_cap(session: AsyncSession, user_id: UUID, tier: str) -> None:
    """Reject analyses beyond the tier's configured per-day limit."""
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    used = await session.scalar(
        select(func.count())
        .select_from(AnalysisModel)
        .where(
            AnalysisModel.user_id == user_id,
            AnalysisModel.created_at >= start_of_day,
        )
    )
    limit = _tier_daily_limit(tier)
    if (used or 0) >= limit:
        raise RateLimitError(f"Daily analysis limit of {limit} reached")


class AnalysisService:
    """Analysis use cases bound to the request session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_analysis(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        analysis_type: str = "general",
        target_role: str | None = None,
        job_description: str | None = None,
        custom_instructions: str | None = None,
        tier: str = "free",
        schedule: bool = True,
    ) -> AnalysisModel:
        """Validate the request, insert a queued analysis, schedule the run.

        Args:
            user_id: Owner (must also own the resume).
            resume_id: Resume to roast (must exist and not be soft-deleted).
            analysis_type: ``general`` always; ``role_based`` needs
                ``target_role``; ``jd_based`` needs ``job_description``;
                ``custom`` leans into ``custom_instructions``.
            schedule: False in tests that drive ``_execute_pipeline`` directly.

        Raises:
            ValidationError: Unknown mode, or missing mode-required context.
            NotFoundError: Resume missing, not owned, or soft-deleted.
            RateLimitError: Daily tier cap reached.
        """
        if not get_evaluators_for_mode(analysis_type):
            raise ValidationError(
                f"Analysis type '{analysis_type}' is not available yet; use 'general'"
            )
        if analysis_type == "role_based" and not (target_role or "").strip():
            raise ValidationError(
                "role_based analysis requires target_role (pick a role)"
            )
        if analysis_type == "jd_based" and not (job_description or "").strip():
            raise ValidationError(
                "jd_based analysis requires job_description (paste the posting)"
            )

        resume = await self._session.get(ResumeModel, resume_id)
        if resume is None or resume.user_id != user_id or resume.deleted_at is not None:
            raise NotFoundError("Resume not found")

        await _enforce_daily_cap(self._session, user_id, tier)

        analysis = AnalysisModel(
            user_id=user_id,
            resume_id=resume_id,
            analysis_type=analysis_type,
            target_role=target_role,
            job_description=job_description,
            custom_instructions=custom_instructions,
            status="queued",
        )
        self._session.add(analysis)
        await self._session.commit()
        if schedule:
            schedule_pipeline(analysis.id)
        return analysis

    async def list_analyses(
        self, *, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[AnalysisModel], int]:
        """The user's analyses, newest first, with their results loaded."""
        items = (
            await self._session.scalars(
                select(AnalysisModel)
                .where(AnalysisModel.user_id == user_id)
                .options(selectinload(AnalysisModel.result))
                .order_by(AnalysisModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
        total = await self._session.scalar(
            select(func.count())
            .select_from(AnalysisModel)
            .where(AnalysisModel.user_id == user_id)
        )
        return list(items), int(total or 0)

    async def get_analysis(self, *, user_id: UUID, analysis_id: UUID) -> AnalysisModel:
        """One analysis with its result; 404 unless owned by ``user_id``."""
        analysis = await self._session.scalar(
            select(AnalysisModel)
            .options(selectinload(AnalysisModel.result))
            .where(AnalysisModel.id == analysis_id)
        )
        if analysis is None or analysis.user_id != user_id:
            raise NotFoundError("Analysis not found")
        return analysis


def schedule_pipeline(analysis_id: UUID) -> asyncio.Task:
    """Fire-and-forget the pipeline; status lives in the DB, not the request."""
    return asyncio.create_task(run_pipeline(analysis_id))


async def run_pipeline(analysis_id: UUID, session_factory: Any = None) -> None:
    """Run the roast pipeline in its own session.

    The factory is injectable so tests can run the pipeline inside the
    test transaction instead of opening a real one.
    """
    factory = session_factory or get_session_factory()
    async with factory() as session:
        await _execute_pipeline(session, analysis_id)


async def _set_stage(
    session: AsyncSession, analysis: AnalysisModel, stage: str
) -> None:
    """Persist a stage transition so status polls see live progress."""
    analysis.status = stage
    await session.commit()


def _analysis_context(analysis: AnalysisModel) -> dict[str, Any]:
    """Analysis context for the evaluators (mode-specific mode inputs).

    ``role_slug`` carries the registered role-context prompt when the
    user's target_role matches one; unknown roles pass through as text only.
    """
    return {
        "target_role": analysis.target_role,
        "job_description": analysis.job_description,
        "custom_instructions": analysis.custom_instructions,
        "role_slug": (
            analysis.target_role if get_role_context(analysis.target_role) else None
        ),
    }


async def _execute_pipeline(session: AsyncSession, analysis_id: UUID) -> None:
    """The pipeline proper: parse → evaluate → score → compose → persist.

    Never raises: any failure is recorded on the analysis row as status
    ``failed`` with a clean error message (no raw tracebacks upstream).
    """
    started = time.monotonic()
    analysis = await session.get(AnalysisModel, analysis_id)
    if analysis is None:
        logger.error("Pipeline started for missing analysis %s", analysis_id)
        return
    try:
        await _set_stage(session, analysis, "extracting")
        resume = await session.get(ResumeModel, analysis.resume_id)
        raw_text = resume.raw_text if resume is not None else None
        if not raw_text:
            raise AnalysisFailedError("extracting", "resume has no extracted text")

        await _set_stage(session, analysis, "parsing")
        structured = await parse_resume(raw_text)
        if resume is not None:
            resume.structured_data = {
                **(resume.structured_data or {}),
                "parsed": structured.model_dump(),
            }

        await _set_stage(session, analysis, "evaluating")
        evaluations = await run_evaluations(
            structured.model_dump(),
            analysis.analysis_type,
            context=_analysis_context(analysis),
        )

        await _set_stage(session, analysis, "scoring")
        aggregated = aggregate_results(evaluations.outputs, evaluations.failed_names)
        scoring = calculate_scores(
            structured,
            raw_text,
            evaluations.outputs,
            evaluations.failed_names,
            mode=analysis.analysis_type,
        )

        await _set_stage(session, analysis, "composing")
        roast, roast_fallback, composer_usage = await compose_roast(
            aggregated, scoring, custom_instructions=analysis.custom_instructions
        )

        session.add(
            _result_row(
                analysis.id, evaluations, aggregated, scoring, roast, roast_fallback
            )
        )
        for usage in [*evaluations.usage, composer_usage]:
            if usage is None:
                continue
            session.add(
                AnalysisUsageModel(
                    user_id=analysis.user_id,
                    analysis_id=analysis.id,
                    ai_model=usage.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    cost_usd=_cost_usd(usage),
                )
            )

        usage_models = [u.model for u in evaluations.usage if u.model]
        if composer_usage is not None and composer_usage.model:
            usage_models.append(composer_usage.model)
        analysis.status = (
            "partial" if (evaluations.failed or roast_fallback) else "completed"
        )
        analysis.ai_model_used = usage_models[0] if usage_models else None
        analysis.prompt_versions_used = dict(PROMPT_VERSIONS)
        analysis.completed_at = datetime.now(UTC)
        analysis.processing_time_ms = int((time.monotonic() - started) * 1000)
        await session.commit()
        logger.info(
            "Analysis %s finished: status=%s score=%s in %dms",
            analysis_id,
            analysis.status,
            scoring.overall_score,
            analysis.processing_time_ms,
        )
    except Exception as exc:
        logger.exception("Analysis %s failed", analysis_id)
        analysis.status = "failed"
        analysis.error_message = str(exc)[:2000]
        analysis.completed_at = datetime.now(UTC)
        analysis.processing_time_ms = int((time.monotonic() - started) * 1000)
        await session.commit()


def _cost_usd(usage: Any) -> Decimal | None:
    """Call cost from configured per-1M-token prices; None when unpriced."""
    if settings.ai_input_price_per_m is None or settings.ai_output_price_per_m is None:
        return None
    cost = (
        usage.prompt_tokens / 1_000_000 * settings.ai_input_price_per_m
        + usage.completion_tokens / 1_000_000 * settings.ai_output_price_per_m
    )
    return Decimal(str(round(cost, 6)))


def _feedback(outputs: dict[str, Any], name: str) -> dict[str, Any] | None:
    output = outputs.get(name)
    return output.model_dump() if output is not None else None


def _result_row(
    analysis_id: UUID,
    evaluations: Any,
    aggregated: Any,
    scoring: Any,
    roast: str,
    roast_fallback: bool,
) -> AnalysisResultModel:
    """Map pipeline outputs onto the denormalized ``analysis_results`` row."""
    return AnalysisResultModel(
        analysis_id=analysis_id,
        recruiter_feedback=_feedback(evaluations.outputs, "recruiter"),
        ats_feedback=_feedback(evaluations.outputs, "ats"),
        technical_feedback=_feedback(evaluations.outputs, "technical"),
        content_feedback=_feedback(evaluations.outputs, "content_quality"),
        job_match_feedback=_feedback(evaluations.outputs, "job_matcher"),
        critical_issues=[item.model_dump() for item in aggregated.critical_issues],
        warnings=[item.model_dump() for item in aggregated.warnings],
        suggestions=[item.model_dump() for item in aggregated.suggestions],
        positive_notes=aggregated.positive_notes,
        overall_score=scoring.overall_score,
        scoring_breakdown={
            "deterministic_checks": [
                check.model_dump() for check in scoring.deterministic_checks
            ],
            "deterministic_score": scoring.deterministic_score,
            "ai_categories": [c.model_dump() for c in scoring.ai_categories],
            "ai_score": scoring.ai_score,
        },
        scoring_methodology=scoring.methodology,
        final_roast=roast,
        final_report={
            "evaluator_summaries": aggregated.evaluator_summaries,
            "failed_evaluators": aggregated.failed_evaluators,
            "roast_fallback_used": roast_fallback,
        },
    )
