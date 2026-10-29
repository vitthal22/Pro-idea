"""Roast composer — synthesizes the structured reality check (v2).

The composer is the only free-form prose in the pipeline, but since v2 it
returns a **structured** ``RoastReport`` (headline verdict, five-second
impression, poison points, three-market analysis, and the narrative
roast) validated via ``call_ai(response_model=...)``. If the AI call fails
after retries, a deterministic ``RoastReport`` built from the aggregated
findings is returned instead — every field is always populated.
"""

from __future__ import annotations

import json
import logging

from app.ai.prompts.composer import SYSTEM_PROMPT
from app.ai.provider import AIResult, call_ai
from app.common.exceptions import AIEvaluationError
from app.schemas.report import (
    AggregatedResults,
    MarketVerdict,
    RoastReport,
    ScoringResult,
)

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


def _fallback_roast(
    aggregated: AggregatedResults, scoring: ScoringResult
) -> RoastReport:
    """Deterministic RoastReport used when the AI composer fails.

    Every field of the schema is populated so the UI never has to handle
    a partial reality check.
    """
    score_line = f"Your resume scores {scoring.overall_score:g}/100."
    headline = (
        f"A resume that will be filtered, not read — {scoring.overall_score:g}/100."
    )
    critical_texts = [item.text for item in aggregated.critical_issues[:3]]
    poison = (
        critical_texts
        or [item.text for item in aggregated.warnings[:2]]
        or [
            "No fatal findings surfaced — but nothing impressive did either.",
        ]
    )
    markets = [
        MarketVerdict(
            market="Product Tech & Tier-1",
            verdict=(
                "strong fit"
                if scoring.overall_score >= 75
                else "borderline / screen fail"
                if scoring.overall_score >= 45
                else "high rejection risk"
            ),
            analysis=(
                f"Deterministic checks score {scoring.deterministic_score:g}/100 "
                "and expert ratings "
                f"{scoring.ai_score:g}/100 — tier-1 product teams read the gap "
                "as missing ownership evidence."
            ),
            missing_signals=[item.text for item in aggregated.warnings[:2]],
        ),
        MarketVerdict(
            market="Service & Consulting",
            verdict=(
                "billable fit with caveats"
                if scoring.overall_score >= 60
                else "high rejection risk"
            ),
            analysis=(
                "Consulting screens look for breadth and client-ready signals; "
                "the findings above define the caveats."
            ),
            missing_signals=[],
        ),
        MarketVerdict(
            market="2026 AI-Era Market",
            verdict="high rejection risk"
            if scoring.overall_score < 70
            else "borderline / screen fail",
            analysis=(
                "Panels now assume AI-written resumes and trust only "
                "production metrics (P99/SLIs, eval pass rates, cost or "
                "token budgets) — none of which the findings surface."
            ),
            missing_signals=[
                "No verifiable system-scale metrics (P99/SLIs, error budgets)",
                "No evaluation rigor signals (eval pass rates, RAGAS/LangSmith)",
                "No cost or token-budget awareness",
            ],
        ),
    ]
    roast_body = _fallback_roast_prose(aggregated, scoring)
    return RoastReport(
        headline_verdict=headline,
        verdict_summary=score_line
        + " The blunt version of the expert review follows — fix the poison "
        "points before reapplying.",
        five_second_impression=(
            '"Another generic resume — nothing here proves a human with '
            'ownership wrote it. Pass."'
        ),
        poison_points=poison,
        market_analysis=markets,
        roast=roast_body,
    )


def _fallback_roast_prose(aggregated: AggregatedResults, scoring: ScoringResult) -> str:
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
) -> tuple[RoastReport, bool, AIResult | None]:
    """Compose the structured reality check + narrative roast.

    Args:
        aggregated: Deduplicated expert findings.
        scoring: The hybrid scoring result (score + context for the roast).
        custom_instructions: The user's own focus areas (``custom`` mode) —
            the roast leans into what they asked to be judged on.

    Returns:
        ``(report, fallback_used, usage)`` — ``fallback_used`` is True when
        the AI pass failed and the deterministic template was served;
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
        "Write the verdict from these expert findings:\n\n"
        "FINDINGS (JSON):\n"
        f"{json.dumps(_compact(aggregated, scoring), ensure_ascii=False)}"
        f"{focus}"
    )
    try:
        result = await call_ai(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=RoastReport,
        )
        report = result.data
        if not isinstance(report, RoastReport):
            raise AIEvaluationError(
                evaluator="composer", reason="model returned no structured verdict"
            )
        return report, False, result
    except AIEvaluationError:
        logger.warning("Roast composer failed — serving deterministic fallback")
        return _fallback_roast(aggregated, scoring), True, None
