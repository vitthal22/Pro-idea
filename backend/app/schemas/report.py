"""Pydantic schemas for pipeline outputs: aggregated findings and scores.

These serialize into the JSONB columns of ``analysis_results`` (Phase 3),
so the field names here are the API contract for the frontend result view.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReportItem(BaseModel):
    """One finding, with the evaluator that raised it."""

    text: str = Field(description="The finding, quoting the resume where relevant")
    source: str = Field(description="Evaluator that raised it (e.g. 'recruiter')")


class AggregatedResults(BaseModel):
    """Deterministic merge of all evaluator outputs.

    Produced by ``app.ai.aggregator`` — findings are deduplicated across
    evaluators and ranked into critical issues → warnings → suggestions →
    positives. Both perspectives coexist (recruiter says X, technical says Y).
    """

    critical_issues: list[ReportItem] = Field(
        default_factory=list,
        description="Deal-breakers a recruiter would hold against the candidate",
    )
    warnings: list[ReportItem] = Field(
        default_factory=list,
        description="Credibility doubts, gaps, formatting and clarity problems",
    )
    suggestions: list[ReportItem] = Field(
        default_factory=list,
        description="Concrete rewrites and additions the candidate can act on",
    )
    positive_notes: list[str] = Field(
        default_factory=list,
        description="Well-evidenced strengths worth keeping",
    )
    evaluator_summaries: dict[str, str] = Field(
        default_factory=dict,
        description="Per-evaluator two-sentence verdicts (surviving evaluators only)",
    )
    failed_evaluators: list[str] = Field(
        default_factory=list,
        description="Evaluators that failed; the result is based on the rest",
    )


class DeterministicCheck(BaseModel):
    """One code-computed scoring check (reproducible, no AI)."""

    name: str = Field(description="Check name (e.g. 'quantified_achievements')")
    score: float = Field(ge=0, description="Points earned")
    max: float = Field(gt=0, description="Maximum points for this check")
    details: str = Field(description="What drove the score")


class CategoryScore(BaseModel):
    """One AI-rated scoring category, mapped deterministically to points."""

    category: str = Field(description="Scoring category (e.g. 'content_quality')")
    rating: str = Field(description="Categorical rating from the evaluator")
    score: float = Field(ge=0, le=100, description="Category score within its band")
    weight: float = Field(description="Category weight before renormalization")
    details: str = Field(description="How the rating was mapped to points")


class ScoringResult(BaseModel):
    """Hybrid score: deterministic checks (50%) + AI ratings (50%).

    When every AI evaluator failed, the score falls back to deterministic-
    only (100%) and ``methodology["ai_partial"]`` says so. Identical inputs
    and identical success/failure patterns always produce identical scores.
    """

    overall_score: float = Field(ge=0, le=100, description="Final 0-100 score")
    deterministic_checks: list[DeterministicCheck] = Field(default_factory=list)
    deterministic_score: float = Field(
        ge=0, le=100, description="Deterministic checks, normalized to 0-100"
    )
    ai_categories: list[CategoryScore] = Field(
        default_factory=list,
        description="Surviving AI-rated categories (failed ones are dropped)",
    )
    ai_score: float = Field(
        ge=0, le=100, description="Renormalized weighted AI categories, 0-100"
    )
    methodology: dict[str, Any] = Field(
        default_factory=dict,
        description="Weights used, renormalization and partial-failure flags",
    )


class MarketVerdict(BaseModel):
    """How one hiring market would treat this resume (composer output)."""

    market: Literal[
        "Product Tech & Tier-1", "Service & Consulting", "2026 AI-Era Market"
    ] = Field(description="The hiring market being judged")
    verdict: Literal[
        "strong fit",
        "billable fit with caveats",
        "borderline / screen fail",
        "high rejection risk",
    ] = Field(description="How the resume fares in this market")
    analysis: str = Field(
        max_length=400,
        description="Why this market reacts that way — grounded in the findings",
    )
    missing_signals: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Market-specific evidence the resume lacks (e.g. 'No "
        "evidence of P99 latency SLAs', 'No mention of LLM evaluation "
        "frameworks (e.g. RAGAS, LangSmith)')",
    )


class RoastReport(BaseModel):
    """Structured reality-check produced by the composer (v2).

    Stored under ``analysis_results.final_report["reality_check"]`` and
    rendered by the result page's scorecard + "Unfiltered Recruiter
    Reality Check" sections.
    """

    headline_verdict: str = Field(
        max_length=140,
        description="One brutal line naming what this resume IS, not what "
        "it contains. e.g. 'Junior task-executor posing as an AI engineer.'",
    )
    verdict_summary: str = Field(
        max_length=500,
        description="Two sentences expanding the headline with the core "
        "problem and its consequence",
    )
    five_second_impression: str = Field(
        max_length=300,
        description="First-person quote of what a recruiter says after the "
        "five-second scan — why the resume gets passed over",
    )
    poison_points: list[str] = Field(
        max_length=5,
        description="Fatal application flaws — one specific sentence each, "
        "grounded in the findings",
    )
    market_analysis: list[MarketVerdict] = Field(
        min_length=3,
        max_length=3,
        description="Exactly the three markets, in order: Product Tech & "
        "Tier-1, Service & Consulting, 2026 AI-Era Market",
    )
    roast: str = Field(
        description="The narrative roast, 200-350 words of flowing prose"
    )
