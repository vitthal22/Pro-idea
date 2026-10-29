"""Result aggregator — deterministic merge of evaluator outputs.

No AI here (ARCHITECTURE §6): findings are deduplicated across evaluators
and ranked into critical issues → warnings → suggestions → positives. The
mapping from evaluator fields to severity buckets is fixed, so identical
evaluator outputs always aggregate identically.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)
from app.schemas.report import AggregatedResults, ReportItem

_NORMALIZE_RE = re.compile(r"[^a-z0-9 ]+")


def _dedupe(items: list[ReportItem]) -> list[ReportItem]:
    """Drop items whose normalized text was already seen."""
    seen: set[str] = set()
    unique: list[ReportItem] = []
    for item in items:
        key = " ".join(_NORMALIZE_RE.sub(" ", item.text.lower()).split())
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def aggregate_results(
    outputs: dict[str, BaseModel], failed_evaluators: list[str]
) -> AggregatedResults:
    """Merge evaluator outputs into a deduplicated, ranked report.

    Args:
        outputs: Surviving evaluator outputs by name (from the orchestrator).
        failed_evaluators: Names of evaluators that failed; recorded so the
            UI can say the result is partial.
    """
    recruiter_out = outputs.get("recruiter")
    recruiter = (
        recruiter_out if isinstance(recruiter_out, RecruiterEvaluatorOutput) else None
    )
    technical_out = outputs.get("technical")
    technical = (
        technical_out if isinstance(technical_out, TechnicalEvaluatorOutput) else None
    )
    ats_out = outputs.get("ats")
    ats = ats_out if isinstance(ats_out, ATSEvaluatorOutput) else None
    content_out = outputs.get("content_quality")
    content = (
        content_out if isinstance(content_out, ContentQualityEvaluatorOutput) else None
    )

    critical_issues: list[ReportItem] = []
    warnings: list[ReportItem] = []
    suggestions: list[ReportItem] = []
    positive_notes: list[str] = []
    evaluator_summaries: dict[str, str] = {}

    if recruiter is not None:
        critical_issues += [
            ReportItem(text=t, source="recruiter") for t in recruiter.red_flags
        ]
        warnings += [
            ReportItem(text=t, source="recruiter") for t in recruiter.credibility_flags
        ]
        evaluator_summaries["recruiter"] = recruiter.summary
        if recruiter.would_shortlist and recruiter.would_shortlist_reason:
            positive_notes.append(recruiter.would_shortlist_reason)

    if technical is not None:
        warnings += [ReportItem(text=t, source="technical") for t in technical.gaps]
        positive_notes += technical.strengths
        evaluator_summaries["technical"] = technical.summary

    if ats is not None:
        warnings += [ReportItem(text=t, source="ats") for t in ats.formatting_issues]
        suggestions += [
            ReportItem(
                text=f"Add {keyword} if you have real experience with it — "
                "ATS filters commonly expect it",
                source="ats",
            )
            for keyword in ats.missing_keywords
        ]
        evaluator_summaries["ats"] = ats.summary

    if content is not None:
        warnings += [
            ReportItem(text=t, source="content_quality")
            for t in content.clarity_findings
        ]
        suggestions += [
            ReportItem(
                text=f'Rewrite the generic phrasing "{t}" with something only you '
                "could have written",
                source="content_quality",
            )
            for t in content.generic_language_issues
        ]
        evaluator_summaries["content_quality"] = content.summary

    return AggregatedResults(
        critical_issues=_dedupe(critical_issues),
        warnings=_dedupe(warnings),
        suggestions=_dedupe(suggestions),
        positive_notes=list(dict.fromkeys(positive_notes)),
        evaluator_summaries=evaluator_summaries,
        failed_evaluators=failed_evaluators,
    )
