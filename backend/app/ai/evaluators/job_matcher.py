"""Job Matcher evaluator — resume fit against a target role or JD.

Requires analysis context: ``target_role`` (role_based) or
``job_description`` (jd_based). Without context the evaluator fails fast —
a fit judgment with nothing to fit against would be fabricated.
"""

from __future__ import annotations

from typing import Any

from app.ai.evaluators.base import run_evaluator
from app.ai.prompts.evaluators.job_matcher import SYSTEM_PROMPT
from app.ai.prompts.roles import get_role_context
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.schemas.evaluators import JobMatchEvaluatorOutput


async def run_job_matcher_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[JobMatchEvaluatorOutput, AIResult]:
    """Judge the resume's fit against the provided role or job description."""
    if not context or not (
        context.get("target_role") or context.get("job_description")
    ):
        raise AIEvaluationError(
            evaluator="job_matcher",
            reason="job matcher requires a target_role or job_description context",
        )

    system_prompt = SYSTEM_PROMPT
    role_slug = context.get("role_slug")
    if role_slug:
        role_prompt = get_role_context(role_slug)
        if role_prompt:
            system_prompt = f"{system_prompt}\n\nROLE CONTEXT:\n{role_prompt}"

    return await run_evaluator(
        name="job_matcher",
        system_prompt=system_prompt,
        response_model=JobMatchEvaluatorOutput,
        resume_data=resume_data,
        context=context,
    )
