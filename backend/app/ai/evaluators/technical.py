"""Technical evaluator — evidence-based technical credibility lens."""

from __future__ import annotations

from typing import Any

from app.ai.evaluators.base import run_evaluator
from app.ai.prompts.evaluators.technical import SYSTEM_PROMPT
from app.ai.provider import AIResult
from app.schemas.evaluators import TechnicalEvaluatorOutput


async def run_technical_evaluator(
    resume_data: dict[str, Any],
) -> tuple[TechnicalEvaluatorOutput, AIResult]:
    """Judge technical depth: evidenced work versus claimed skills."""
    return await run_evaluator(
        name="technical",
        system_prompt=SYSTEM_PROMPT,
        response_model=TechnicalEvaluatorOutput,
        resume_data=resume_data,
    )
