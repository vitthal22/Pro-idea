"""Unit tests for the v2 roast composer (call_ai mocked — no real API)."""

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
    "roast": "Your resume has real problems, and here they are in order.",
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
            data=RoastReport.model_validate(_REPORT_PAYLOAD),
        )

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is False
    assert usage is not None
    assert report.headline_verdict == _REPORT_PAYLOAD["headline_verdict"]
    assert report.roast == _REPORT_PAYLOAD["roast"]
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
        return AIResult(
            content="roast",
            model="m",
            data=RoastReport.model_validate(_REPORT_PAYLOAD),
        )

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
    assert report.roast
    assert "58.4/100" in report.roast
    assert "Nine-month gap unexplained" in report.roast


async def test_compose_roast_falls_back_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs: Any):
        return AIResult(content="   ", model="m")

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    report, fallback, _ = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    assert report.roast


def test_fallback_never_raises_even_from_empty_findings() -> None:
    empty = AggregatedResults()
    report = composer_module._fallback_roast(empty, _scoring())
    assert "58.4/100" in report.roast
    assert "unavailable" in report.roast
    assert len(report.market_analysis) == 3
