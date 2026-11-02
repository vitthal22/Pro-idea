"""Unit tests for the deterministic result aggregator."""

from app.ai.aggregator import aggregate_results
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)

_RECRUITER = RecruiterEvaluatorOutput(
    summary="Solid mid-level resume.",
    first_impression="average",
    first_impression_reason="Generic opener.",
    experience_relevance_rating="good",
    credibility_rating="medium",
    credibility_flags=["Seniority jump without detail"],
    red_flags=["Nine-month gap unexplained"],
    would_shortlist=True,
    would_shortlist_reason="Relevant recent experience",
)
_TECHNICAL = TechnicalEvaluatorOutput(
    summary="Backend evidenced.",
    technical_depth_rating="good",
    gaps=["Kubernetes claimed but never used"],
    strengths=["API latency work quantified"],
)
_ATS = ATSEvaluatorOutput(
    summary="Mostly parseable.",
    ats_readiness_rating="fair",
    formatting_issues=["Two-column header"],
    missing_keywords=["CI/CD"],
)
_CONTENT = ContentQualityEvaluatorOutput(
    summary="Clear but generic.",
    writing_quality_rating="fair",
    generic_language_issues=["passionate team player"],
    quantification_rating="poor",
    clarity_findings=["Two overlapping roles dated 2021"],
)


def _sources(items: list) -> dict[str, list[str]]:
    by_source: dict[str, list[str]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item.text)
    return by_source


def test_findings_ranked_into_severity_buckets() -> None:
    aggregated = aggregate_results(
        {
            "recruiter": _RECRUITER,
            "technical": _TECHNICAL,
            "ats": _ATS,
            "content_quality": _CONTENT,
        },
        failed_evaluators=[],
    )

    assert aggregated.critical_issues[0].text == "Nine-month gap unexplained"
    assert aggregated.critical_issues[0].source == "recruiter"

    warnings_by_source = _sources(aggregated.warnings)
    assert warnings_by_source["recruiter"] == ["Seniority jump without detail"]
    assert "Kubernetes claimed but never used" in warnings_by_source["technical"]
    assert "Two-column header" in warnings_by_source["ats"]
    assert "Two overlapping roles dated 2021" in warnings_by_source["content_quality"]

    suggestions_text = [item.text for item in aggregated.suggestions]
    assert any("CI/CD" in text for text in suggestions_text)
    assert any("passionate team player" in text for text in suggestions_text)

    assert "Relevant recent experience" in aggregated.positive_notes
    assert "API latency work quantified" in aggregated.positive_notes

    assert aggregated.evaluator_summaries == {
        "recruiter": "Solid mid-level resume.",
        "technical": "Backend evidenced.",
        "ats": "Mostly parseable.",
        "content_quality": "Clear but generic.",
    }
    assert aggregated.failed_evaluators == []


def test_duplicate_findings_deduplicate() -> None:
    # Same finding surfacing from two evaluators, differing only in case,
    # punctuation, and whitespace — must collapse to one warning.
    recruiter = _RECRUITER.model_copy(
        update={"credibility_flags": ["Kubernetes claimed but never used"]}
    )
    technical = _TECHNICAL.model_copy(
        update={"gaps": ["Kubernetes claimed, but never used!", "Unrelated real gap"]}
    )

    aggregated = aggregate_results(
        {"recruiter": recruiter, "technical": technical}, failed_evaluators=[]
    )

    kubernetes_items = [
        item for item in aggregated.warnings if "kubernetes" in item.text.lower()
    ]
    assert len(kubernetes_items) == 1
    assert "Unrelated real gap" in [item.text for item in aggregated.warnings]


def test_failed_evaluators_recorded_and_no_crash_on_empty_outputs() -> None:
    aggregated = aggregate_results(
        {}, failed_evaluators=["technical", "content_quality"]
    )

    assert aggregated.critical_issues == []
    assert aggregated.warnings == []
    assert aggregated.suggestions == []
    assert aggregated.evaluator_summaries == {}
    assert aggregated.failed_evaluators == ["technical", "content_quality"]
