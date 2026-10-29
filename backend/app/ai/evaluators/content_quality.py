"""Content Quality evaluator — craft-of-writing lens."""

from __future__ import annotations

from typing import Any

from app.ai.evaluators.base import run_evaluator
from app.ai.prompts.evaluators.content_quality import SYSTEM_PROMPT
from app.ai.provider import AIResult
from app.schemas.evaluators import ContentQualityEvaluatorOutput


async def run_content_quality_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[ContentQualityEvaluatorOutput, AIResult]:
    """Judge the writing itself: clarity, generic language, quantification."""
    return await run_evaluator(
        name="content_quality",
        system_prompt=SYSTEM_PROMPT,
        response_model=ContentQualityEvaluatorOutput,
        resume_data=resume_data,
        context=context,
    )
