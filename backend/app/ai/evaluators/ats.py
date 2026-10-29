"""ATS evaluator — automated parsing and keyword-readiness lens."""

from __future__ import annotations

from typing import Any

from app.ai.evaluators.base import run_evaluator
from app.ai.prompts.evaluators.ats import SYSTEM_PROMPT
from app.ai.provider import AIResult
from app.schemas.evaluators import ATSEvaluatorOutput


async def run_ats_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[ATSEvaluatorOutput, AIResult]:
    """Judge how the resume fares in automated parsing and ranking."""
    return await run_evaluator(
        name="ats",
        system_prompt=SYSTEM_PROMPT,
        response_model=ATSEvaluatorOutput,
        resume_data=resume_data,
        context=context,
    )
