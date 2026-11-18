"""Roast composer — synthesizes the three-hit verdict (v3).

The composer is the only free-form prose in the pipeline, but since v2 it
returns a **structured** ``RoastReport`` (headline verdict, three roast
lines, poison points, three-market analysis) validated via
``call_ai(response_model=...)``.

Since v3 the roast is three one-line hits instead of a 200-350 word essay,
and ``_normalize`` enforces that shape deterministically: the verdict screen
can never be handed a wall of text, whichever model answered. If the AI call
fails after retries, a deterministic ``RoastReport`` built from the
aggregated findings is returned instead — every field is always populated.
"""

from __future__ import annotations

import json
import logging
import re

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

# The shape the UI renders. These are targets, not schema limits: the schema
# stays looser on purpose, because a validation failure spends a retry and
# then the deterministic fallback. Shape is enforced here instead.
_ROAST_LINE_COUNT = 3
_ROAST_LINE_CHARS = 110
_POISON_POINT_COUNT = 3
_POISON_POINT_CHARS = 160
_MARKET_ANALYSIS_CHARS = 190
_MISSING_SIGNAL_COUNT = 2
_MISSING_SIGNAL_CHARS = 80
_SUMMARY_CHARS = 260
_IMPRESSION_CHARS = 170
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_LIST_MARKER = re.compile(r"^(?:[-*•–—]+\s*|\d+[.)]\s*)")
_WRAPPING_QUOTES = "\"'“”‘’"
# Two findings making the same point share most of their content words.
_DUPLICATE_OVERLAP = 0.55
_STOPWORDS = frozenset(
    "a an and are as at be but by for from has have in into is it its of on or "
    "that the their this to was were with your you without not no".split()
)


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


def _collapse(text: str) -> str:
    """One line, single spaces, no stray whitespace."""
    return " ".join(text.split())


def _tokens(text: str) -> set[str]:
    """Content words, for spotting two findings that say the same thing."""
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return {
        word for word in cleaned.split() if len(word) > 2 and word not in _STOPWORDS
    }


def _is_repeat(tokens: set[str], seen: list[set[str]]) -> bool:
    """True when a finding restates one already kept (Jaccard overlap)."""
    if not tokens:
        return True
    return any(
        len(tokens & previous) / len(tokens | previous) >= _DUPLICATE_OVERLAP
        for previous in seen
    )


def _clip_words(text: str, limit: int) -> str:
    """Clip to ``limit`` characters at a word boundary (ellipsis when cut)."""
    text = _collapse(text)
    if len(text) <= limit:
        return text
    head = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:–—-")
    return f"{head}…"


def _clip_sentence(text: str, limit: int) -> str:
    """Clip on the last whole sentence under ``limit``; otherwise on a word."""
    text = _collapse(text)
    if len(text) <= limit:
        return text
    window = text[:limit]
    end = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
    if end >= limit // 2:
        return window[: end + 1]
    return _clip_words(text, limit)


def _clean_line(text: str) -> str:
    """Strip list markers, markdown emphasis and wrapping quotes from a hit."""
    line = _LIST_MARKER.sub("", _collapse(text)).replace("**", "")
    if len(line) >= 2 and line[0] in _WRAPPING_QUOTES and line[-1] in _WRAPPING_QUOTES:
        line = line[1:-1].strip()
    return line


def _clip_line(text: str, limit: int) -> str:
    """A hit is one sentence: keep the first, clip it only if it overflows."""
    text = _collapse(text)
    if len(text) <= limit:
        return text
    first = _SENTENCE_SPLIT.split(text)[0]
    if len(first) <= limit:
        return first
    return _clip_words(text, limit)


def _keep_lines(candidates: list[str]) -> list[str]:
    """Clean, de-duplicate and clip candidates down to three distinct hits."""
    kept: list[str] = []
    seen: list[set[str]] = []
    for candidate in candidates:
        line = _clip_line(_clean_line(candidate), _ROAST_LINE_CHARS)
        tokens = _tokens(line)
        if not line or _is_repeat(tokens, seen):
            continue
        kept.append(line)
        seen.append(tokens)
        if len(kept) == _ROAST_LINE_COUNT:
            break
    return kept


def _normalize(report: RoastReport) -> RoastReport:
    """Force the report into the shape the verdict screen renders.

    The prompt asks for three 110-character hits, three poison points and
    short market lines; models drift long. This pass is deterministic, runs
    on every successful composer call, and is what actually guarantees the
    page never shows an essay.
    """
    lines = list(report.roast_lines)
    if not any(line.strip() for line in lines):
        # A model that ignored ``roast_lines`` still gave us prose: salvage it.
        lines = _SENTENCE_SPLIT.split(report.roast)
    report.roast_lines = _keep_lines(lines)

    points: list[str] = []
    seen: list[set[str]] = []
    for point in report.poison_points:
        text = _clip_sentence(point, _POISON_POINT_CHARS)
        tokens = _tokens(text)
        if not text or _is_repeat(tokens, seen):
            continue
        points.append(text)
        seen.append(tokens)
        if len(points) == _POISON_POINT_COUNT:
            break
    report.poison_points = points

    for market in report.market_analysis:
        market.analysis = _clip_sentence(market.analysis, _MARKET_ANALYSIS_CHARS)
        market.missing_signals = [
            _clip_words(signal, _MISSING_SIGNAL_CHARS)
            for signal in market.missing_signals[:_MISSING_SIGNAL_COUNT]
        ]

    report.verdict_summary = _clip_sentence(report.verdict_summary, _SUMMARY_CHARS)
    report.five_second_impression = _clip_sentence(
        report.five_second_impression, _IMPRESSION_CHARS
    )
    return report


def _fallback_roast_lines(aggregated: AggregatedResults) -> list[str]:
    """Deterministic hits built from the real findings.

    No finding is invented to reach three lines: a sparse report shows fewer
    hits rather than a fabricated defect.
    """
    candidates = [
        item.text for item in (*aggregated.critical_issues, *aggregated.warnings)
    ]
    candidates += [item.text for item in aggregated.suggestions]
    return _keep_lines(candidates)


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
    poison = [item.text for item in aggregated.critical_issues[:2]] or [
        item.text for item in aggregated.warnings[:2]
    ]
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
                f"and expert ratings {scoring.ai_score:g}/100 — tier-1 product "
                "teams read the gap as missing ownership evidence."
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
                "production metrics (P99/SLIs, eval pass rates, cost or token "
                "budgets) — none of which the findings surface."
            ),
            missing_signals=[
                "No verifiable system-scale metrics (P99/SLIs, error budgets)",
                "No evaluation rigor signals (eval pass rates, RAGAS/LangSmith)",
                "No cost or token-budget awareness",
            ],
        ),
    ]
    return RoastReport(
        headline_verdict=headline,
        verdict_summary=score_line
        + " The expert findings below are the reason — fix the poison points "
        "before reapplying.",
        five_second_impression=(
            '"Another generic resume — nothing here proves a human with '
            'ownership wrote it. Pass."'
        ),
        poison_points=poison,
        market_analysis=markets,
        roast_lines=_fallback_roast_lines(aggregated),
        roast="",
    )


async def compose_roast(
    aggregated: AggregatedResults,
    scoring: ScoringResult,
    custom_instructions: str | None = None,
    chain: list[str] | None = None,
) -> tuple[RoastReport, bool, AIResult | None]:
    """Compose the structured reality check + the three-hit roast.

    Args:
        aggregated: Deduplicated expert findings.
        scoring: The hybrid scoring result (score + context for the roast).
        custom_instructions: The user's own focus areas (``custom`` mode) —
            the roast leans into what they asked to be judged on.
        chain: Model cascade override (tier-derived); None uses config.

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
            chain=chain,
        )
        report = result.data
        if not isinstance(report, RoastReport):
            raise AIEvaluationError(
                evaluator="composer", reason="model returned no structured verdict"
            )
        report = _normalize(report)
        if not report.roast_lines:
            raise AIEvaluationError(
                evaluator="composer", reason="model returned no roast lines"
            )
        return report, False, result
    except AIEvaluationError:
        logger.warning("Roast composer failed — serving deterministic fallback")
        return _normalize(_fallback_roast(aggregated, scoring)), True, None
