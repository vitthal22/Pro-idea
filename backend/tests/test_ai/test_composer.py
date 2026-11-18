"""Unit tests for the v3 roast composer (call_ai mocked — no real API)."""

import json
from typing import Any

import pytest

from app.ai import composer as composer_module
from app.ai.composer import compose_roast
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.schemas.report import AggregatedResults, ReportItem, RoastReport, ScoringResult

_REPORT_PAYLOAD: dict[str, Any] = {
    "headline_verdict": "Junior task-executor posing as an AI engineer.",
    "verdict_summary": (
        "Your resume reads like a list of Jira tickets, not business value."
    ),
    "five_second_impression": (
        '"Another React/Python developer with a laundry list of libraries. '
        'No system architecture, no scale. Pass."'
    ),
    "poison_points": [
        "No mention of handling system failures or edge-case reliability.",
        "Techno-babble heavy (stack-stuffing) without deeper engineering.",
    ],
    "market_analysis": [
        {
            "market": "Product Tech & Tier-1",
            "verdict": "borderline / screen fail",
            "analysis": "Reads like a feature implementer, not an owner.",
            "missing_signals": ["No evidence of P99 latency SLAs"],
        },
        {
            "market": "Service & Consulting",
            "verdict": "billable fit with caveats",
            "analysis": "Lacks enterprise certifications for client work.",
            "missing_signals": [],
        },
        {
            "market": "2026 AI-Era Market",
            "verdict": "high rejection risk",
            "analysis": "Builds WITH AI models but shows no eval rigor.",
            "missing_signals": ["No cost-per-inference metrics"],
        },
    ],
    "roast_lines": [
        "Nine months unaccounted for, and no line in the resume explains them.",
        "Kubernetes is claimed but never appears in any project you shipped.",
        "Three years of work, zero numbers — every claim is an adjective.",
    ],
    "roast": "",
}


def _aggregated() -> AggregatedResults:
    return AggregatedResults(
        critical_issues=[
            ReportItem(text="Nine-month gap unexplained", source="recruiter")
        ],
        warnings=[
            ReportItem(text="Kubernetes claimed but never used", source="technical")
        ],
        suggestions=[
            ReportItem(text="Rewrite the generic opener", source="content_quality")
        ],
        positive_notes=["API latency work quantified"],
        evaluator_summaries={"recruiter": "Solid."},
        failed_evaluators=[],
    )


def _scoring() -> ScoringResult:
    return ScoringResult(
        overall_score=58.4,
        deterministic_score=61.3,
        ai_score=55.5,
        methodology={"ai_partial": False, "failed_evaluators": []},
    )


def _report(**overrides: Any) -> RoastReport:
    payload = {**_REPORT_PAYLOAD, **overrides}
    return RoastReport.model_validate(payload)


async def test_compose_roast_returns_structured_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_ai(**kwargs: Any):
        captured.update(kwargs)
        return AIResult(
            content=json.dumps(_REPORT_PAYLOAD),
            model="gemini/gemini-3.5-flash",
            prompt_tokens=100,
            completion_tokens=200,
            data=_report(),
        )

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is False
    assert usage is not None
    assert report.headline_verdict == _REPORT_PAYLOAD["headline_verdict"]
    assert report.roast_lines == _REPORT_PAYLOAD["roast_lines"]
    assert len(report.market_analysis) == 3
    # The structured call is prompted with the findings JSON.
    assert '"overall_score": 58.4' in captured["user_prompt"]
    assert "Nine-month gap unexplained" in captured["user_prompt"]


async def test_compose_roast_user_focus_reaches_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_ai(**kwargs: Any):
        captured.update(kwargs)
        return AIResult(content="roast", model="m", data=_report())

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    await compose_roast(
        _aggregated(), _scoring(), custom_instructions="Tear apart my bullets"
    )

    assert "USER FOCUS" in captured["user_prompt"]
    assert "Tear apart my bullets" in captured["user_prompt"]


async def test_compose_roast_falls_back_with_full_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs: Any):
        raise AIEvaluationError(evaluator="composer", reason="provider down")

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    assert usage is None
    # Every field of the schema is populated — the UI never sees a partial
    # reality check.
    assert report.headline_verdict
    assert report.verdict_summary
    assert report.five_second_impression
    assert report.poison_points
    assert len(report.market_analysis) == 3
    assert all(market.analysis for market in report.market_analysis)
    # The roast is still short in the degraded path.
    assert len(report.roast_lines) == 3
    assert all(len(line) <= 110 for line in report.roast_lines)
    assert "Nine-month gap unexplained" in report.roast_lines
    assert "58.4/100" in report.verdict_summary


async def test_compose_roast_falls_back_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs: Any):
        return AIResult(content="   ", model="m")

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, _ = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    assert report.roast_lines


async def test_compose_roast_falls_back_without_roast_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A verdict with no usable hit is not a verdict — degrade instead."""

    async def fake_call_ai(**kwargs: Any):
        return AIResult(content="{}", model="m", data=_report(roast_lines=[], roast=""))

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, _ = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    assert len(report.roast_lines) == 3


def test_roast_lines_are_capped_at_three_short_hits() -> None:
    report = _report(
        roast_lines=[
            "One: the skills wall has forty entries and no proof behind any of them.",
            "Two: the timeline overlaps by fourteen months and nobody explains it.",
            "Three: every bullet claims ownership but none names a system or a metric.",
            "Four: this line should never reach the page because three is the cap.",
            "Five: neither should this one, no matter how well it is written today.",
        ]
    )

    normalized = composer_module._normalize(report)

    assert len(normalized.roast_lines) == 3
    assert normalized.roast_lines[0].startswith("One:")
    assert normalized.roast_lines[-1].startswith("Three:")


def test_overlong_hit_is_clipped_at_a_word_boundary() -> None:
    long_line = (
        "Your resume lists every technology you have ever opened in a browser and "
        "never once names a system you actually operated in production for a year"
    )
    normalized = composer_module._normalize(_report(roast_lines=[long_line]))

    assert len(normalized.roast_lines) == 1
    assert len(normalized.roast_lines[0]) <= 110
    assert normalized.roast_lines[0].endswith("…")
    assert not normalized.roast_lines[0].endswith(" …")


def test_long_hit_keeps_its_first_sentence() -> None:
    """A hit that runs two sentences is cut to the one that lands."""
    normalized = composer_module._normalize(
        _report(
            roast_lines=[
                "Your MCA runs to 2026 while you claim to have worked since 2024. "
                "Pick one story and delete the other, because both cannot be true "
                "and recruiters do verify dates."
            ]
        )
    )

    assert normalized.roast_lines == [
        "Your MCA runs to 2026 while you claim to have worked since 2024."
    ]


def test_markdown_and_list_markers_are_stripped() -> None:
    normalized = composer_module._normalize(
        _report(roast_lines=['- **"Reduced bugs by 25%"** with no baseline'])
    )

    assert normalized.roast_lines == ['"Reduced bugs by 25%" with no baseline']


def test_duplicate_hits_are_dropped() -> None:
    line = "Kubernetes is claimed but never appears in any project you shipped"
    normalized = composer_module._normalize(
        _report(roast_lines=[line, line, "Zero numbers in three years of work"])
    )

    assert normalized.roast_lines == [line, "Zero numbers in three years of work"]


def test_prose_only_response_is_salvaged_into_hits() -> None:
    """A model that ignores ``roast_lines`` must not cost a fallback."""
    normalized = composer_module._normalize(
        _report(
            roast_lines=[],
            roast=(
                "Your resume is a keyword dump. You list forty technologies. "
                "Nobody measured any of it."
            ),
        )
    )

    assert normalized.roast_lines == [
        "Your resume is a keyword dump.",
        "You list forty technologies.",
        "Nobody measured any of it.",
    ]


def test_poison_points_are_capped_and_deduplicated() -> None:
    point = "No production metrics anywhere on the resume"
    normalized = composer_module._normalize(
        _report(
            poison_points=[
                point,
                point,
                "Timeline overlaps by fourteen months",
                "Skills list is a stack dump with no depth",
                "No contact information on page one",
            ]
        )
    )

    assert normalized.poison_points == [
        point,
        "Timeline overlaps by fourteen months",
        "Skills list is a stack dump with no depth",
    ]


def test_market_analysis_and_summary_are_shortened() -> None:
    long_analysis = (
        "Tier-1 product teams expect ownership evidence: the systems you operated, "
        "the latency you held, the incidents you led, and the cost per request you "
        "reduced. None of that appears anywhere in this resume, so the screen fails."
    )
    normalized = composer_module._normalize(
        _report(
            verdict_summary="One. " * 80,
            market_analysis=[
                {
                    "market": "Product Tech & Tier-1",
                    "verdict": "high rejection risk",
                    "analysis": long_analysis,
                    "missing_signals": [
                        "No verifiable system-scale metrics: no P99 latency, "
                        "no error budget and no on-call ownership anywhere",
                        "b",
                        "c",
                    ],
                },
                *_REPORT_PAYLOAD["market_analysis"][1:],
            ],
        )
    )

    assert len(normalized.market_analysis[0].analysis) <= 190
    assert len(normalized.market_analysis[0].missing_signals) == 2
    assert all(
        len(signal) <= 80 for signal in normalized.market_analysis[0].missing_signals
    )
    assert len(normalized.verdict_summary) <= 260


def test_fallback_never_raises_even_from_empty_findings() -> None:
    empty = AggregatedResults()
    report = composer_module._normalize(
        composer_module._fallback_roast(empty, _scoring())
    )

    # No findings means no hits — never a fabricated defect.
    assert report.roast_lines == []
    assert "58.4/100" in report.verdict_summary
    assert len(report.market_analysis) == 3
