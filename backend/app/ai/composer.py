"""Roast composer — synthesizes the final roast from aggregated findings.

The composer is the only free-form prose in the pipeline. If the AI call
fails after retries, a deterministic template of the aggregated findings is
returned instead (never an exception up the stack): a degraded roast beats
a failed analysis.
"""

from __future__ import annotations

import json
import logging

from app.ai.prompts.composer import SYSTEM_PROMPT
from app.ai.provider import AIResult, call_ai
from app.common.exceptions import AIEvaluationError
from app.schemas.report import AggregatedResults, ScoringResult

logger = logging.getLogger("app.ai.composer")

_MAX_ITEMS_PER_LIST = 8
_MAX_ITEM_CHARS = 160


def _compact(
    aggregated: AggregatedResults, scoring: ScoringResult
) -> dict[str, object]:
    """Compact JSON view of the findings, within the composer's budget."""

    def clip(items: list[str]) -> list[str]:
        return [item[:_MAX_ITEM_CHARS] for item in items[:_MAX_ITEMS_PER_LIST]]

    return {
        "overall_score": scoring.overall_score,
        "score_context": {
            "deterministic_score": scoring.deterministic_score,
            "ai_score": scoring.ai_score,
            "ai_partial": scoring.methodology.get("ai_partial", False),
            "failed_evaluators": scoring.methodology.get("failed_evaluators", []),
        },
        "critical_issues": clip([i.text for i in aggregated.critical_issues]),
        "warnings": clip([i.text for i in aggregated.warnings]),
        "suggestions": clip([i.text for i in aggregated.suggestions]),
        "positive_notes": clip(aggregated.positive_notes),
        "evaluator_summaries": aggregated.evaluator_summaries,
    }


def _fallback_roast(aggregated: AggregatedResults, scoring: ScoringResult) -> str:
    """Deterministic roast used when the AI composer fails."""
    lines = [
        f"Your resume scores {scoring.overall_score:g}/100 — here is the blunt "
        "version of the expert review."
    ]
    if aggregated.critical_issues:
        lines.append("The deal-breakers:")
        lines += [f"- {item.text}" for item in aggregated.critical_issues[:5]]
    if aggregated.warnings:
        lines.append("What a reviewer would push back on:")
        lines += [f"- {item.text}" for item in aggregated.warnings[:5]]
    if aggregated.suggestions:
        lines.append("Fix these first:")
        lines += [f"- {item.text}" for item in aggregated.suggestions[:5]]
    if aggregated.positive_notes:
        lines.append("What genuinely works, keep it:")
        lines += [f"- {note}" for note in aggregated.positive_notes[:5]]
    lines.append(
        "(The narrative roast pass was unavailable — this summary is the raw "
        "expert findings.)"
    )
    return "\n".join(lines)


async def compose_roast(
    aggregated: AggregatedResults,
    scoring: ScoringResult,
    custom_instructions: str | None = None,
) -> tuple[str, bool, AIResult | None]:
    """Compose the final roast.

    Args:
        aggregated: Deduplicated expert findings.
        scoring: The hybrid scoring result (score + context for the roast).
        custom_instructions: The user's own focus areas (``custom`` mode) —
            the roast leans into what they asked to be judged on.

    Returns:
        ``(roast_text, fallback_used, usage)`` — ``fallback_used`` is True
        when the AI pass failed and the deterministic template was served;
        ``usage`` carries the composer call's token counts (None on fallback).
    """
    focus = ""
    if custom_instructions and custom_instructions.strip():
        focus = (
            "\n\nUSER FOCUS (the candidate explicitly asked to be judged on "
            "this — roast it hardest):\n"
            f"{custom_instructions.strip()[:500]}"
        )
    user_prompt = (
        "Write the roast from these expert findings:\n\n"
        "FINDINGS (JSON):\n"
        f"{json.dumps(_compact(aggregated, scoring), ensure_ascii=False)}"
        f"{focus}"
    )
    try:
        result = await call_ai(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        roast = result.content.strip()
        if not roast:
            raise AIEvaluationError(
                evaluator="composer", reason="model returned empty roast"
            )
        return roast, False, result
    except AIEvaluationError:
        logger.warning("Roast composer failed — serving deterministic fallback")
        return _fallback_roast(aggregated, scoring), True, None
