"""Fix planner — turns the top findings into optimized rewrites.

A supplementary pipeline step: runs in parallel with the composer, consumes
the aggregated findings plus the structured resume (and, for ``jd_based`` /
``role_based`` runs, the Job Matcher output and the JD/role context), and
produces a structured ``FixPlanReport``. On failure it returns ``(None,
None)`` — the rest of the report is unaffected and the UI simply hides the
section, so a fix-planner failure never degrades the analysis status.
"""

import json
import logging
from typing import Any

from app.ai.evaluators.base import compose_context_lines
from app.ai.prompts.fix_planner import SYSTEM_PROMPT
from app.ai.provider import AIResult, call_ai
from app.common.exceptions import AIEvaluationError
from app.schemas.evaluators import JobMatchEvaluatorOutput
from app.schemas.report import AggregatedResults, FixPlanReport

logger = logging.getLogger("app.ai.fix_planner")

_MAX_ITEMS_PER_LIST = 8
_MAX_ITEM_CHARS = 160


def _compact_findings(aggregated: AggregatedResults) -> dict[str, Any]:
    """Token-budgeted findings JSON (same clipping rules as the composer)."""

    def clip(items: list[Any]) -> list[str]:
        return [item.text[:_MAX_ITEM_CHARS] for item in items[:_MAX_ITEMS_PER_LIST]]

    return {
        "critical_issues": clip(aggregated.critical_issues),
        "warnings": clip(aggregated.warnings),
        "suggestions": clip(aggregated.suggestions),
        "positive_notes": aggregated.positive_notes[:_MAX_ITEMS_PER_LIST],
        "failed_evaluators": aggregated.failed_evaluators,
    }


def _job_match_block(job_match: JobMatchEvaluatorOutput | None) -> str:
    """The Job Matcher's resume-vs-posting gap, when one ran."""
    if job_match is None:
        return ""
    payload = {
        "summary": job_match.summary,
        "match_rating": job_match.match_rating,
        "matched_skills": job_match.matched_skills,
        "missing_skills": job_match.missing_skills,
        "alignment_findings": job_match.alignment_findings,
        "recommendations": job_match.recommendations,
    }
    return (
        "\n\nJOB MATCH ANALYSIS (the resume judged against the target "
        "role/job description):\n" + json.dumps(payload, ensure_ascii=False)
    )


async def plan_fixes(
    aggregated: AggregatedResults,
    resume_data: dict[str, Any],
    job_match: JobMatchEvaluatorOutput | None = None,
    context: dict[str, Any] | None = None,
    chain: list[str] | None = None,
) -> tuple[FixPlanReport | None, AIResult | None]:
    """Rewrite the top findings into optimized resume text.

    Returns ``(plan, usage)``, or ``(None, None)`` when the AI pass fails —
    the pipeline stores no fix plan and stays ``completed``.
    """
    user_prompt = (
        "Findings from the expert panel (JSON):\n"
        + json.dumps(_compact_findings(aggregated), ensure_ascii=False)
        + _job_match_block(job_match)
        + "\n\nRESUME DATA (JSON):\n"
        + json.dumps(resume_data, ensure_ascii=False, default=str)
    )
    context_lines = compose_context_lines(context)
    if context_lines:
        user_prompt += "\n\nANALYSIS CONTEXT:\n" + "\n\n".join(context_lines)

    try:
        result = await call_ai(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=FixPlanReport,
            chain=chain,
        )
    except AIEvaluationError as exc:
        logger.warning("Fix planner failed — serving no fix plan (%s)", exc)
        return None, None

    plan = result.data
    if not isinstance(plan, FixPlanReport):
        logger.warning("Fix planner returned no structured plan — skipping")
        return None, None
    return plan, result
