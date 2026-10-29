"""Unit tests for the hybrid scoring engine (determinism, renormalization)."""

from pydantic import BaseModel

from app.ai.scoring import MODE_WEIGHTS, calculate_scores
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    JobMatchEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)
from app.schemas.resume import ContactInfo, ExperienceItem, StructuredResume

_RAW_TEXT = "Built APIs with FastAPI. Led a team of 3. Reduced latency 40%."

_STRONG_RESUME = StructuredResume(
    contact_info=ContactInfo(name="Jane Doe", email="jane@example.com", phone="555"),
    professional_summary="Backend developer",
    experience=[
        ExperienceItem(
            job_title="Backend Developer",
            company="Acme",
            start_date="Jan 2022",
            bullet_points=[
                "Built REST APIs with FastAPI serving 2M requests daily",
                "Reduced database latency by 40% through indexing",
                "Mentored 3 junior engineers across 2 teams",
            ],
        )
    ],
    education=[],
    skills=["Python", "FastAPI"],
)

_ALL_OUTPUTS: dict[str, BaseModel] = {
    "recruiter": RecruiterEvaluatorOutput(
        summary="Solid.",
        first_impression="strong",
        first_impression_reason="Clear evidence.",
        experience_relevance_rating="good",
        credibility_rating="high",
        would_shortlist=True,
        would_shortlist_reason="Relevant experience",
    ),
    "ats": ATSEvaluatorOutput(summary="Parseable.", ats_readiness_rating="good"),
    "technical": TechnicalEvaluatorOutput(
        summary="Evidenced.", technical_depth_rating="excellent"
    ),
    "content_quality": ContentQualityEvaluatorOutput(
        summary="Decent.", writing_quality_rating="good", quantification_rating="good"
    ),
}


def _empty_resume() -> StructuredResume:
    return StructuredResume(contact_info=ContactInfo())


def test_determinism_same_inputs_same_score() -> None:
    first = calculate_scores(_STRONG_RESUME, _RAW_TEXT, _ALL_OUTPUTS, [])
    second = calculate_scores(_STRONG_RESUME, _RAW_TEXT, _ALL_OUTPUTS, [])

    assert first == second
    assert first.overall_score == second.overall_score


def test_rating_maps_to_fixed_bands() -> None:
    result = calculate_scores(_STRONG_RESUME, _RAW_TEXT, _ALL_OUTPUTS, [])

    ratings = {c.category: c.score for c in result.ai_categories}
    assert ratings["skills_alignment"] == 94.0  # technical depth: excellent
    assert ratings["experience"] == 78.5  # good
    assert ratings["role_relevance"] == 94.0  # strong → excellent band
    assert set(ratings) == set(MODE_WEIGHTS["general"])


def test_job_matcher_drives_role_relevance_when_present() -> None:
    outputs = {
        **_ALL_OUTPUTS,
        "job_matcher": JobMatchEvaluatorOutput(
            summary="Strong fit.",
            match_rating="excellent",
            matched_skills=["Python"],
        ),
    }

    result = calculate_scores(_STRONG_RESUME, _RAW_TEXT, outputs, [], mode="role_based")

    relevance = {c.category: c for c in result.ai_categories}["role_relevance"]
    assert relevance.rating == "excellent"
    assert relevance.score == 94.0
    assert "job_matcher.match_rating" in relevance.details
    # role_based weights apply
    assert result.methodology["mode_weights"] == MODE_WEIGHTS["role_based"]


def test_empty_resume_scores_low() -> None:
    result = calculate_scores(_empty_resume(), "", _ALL_OUTPUTS, [])

    assert result.overall_score < 50
    low_checks = {c.name: c for c in result.deterministic_checks}
    assert low_checks["bullet_points"].score == 0
    assert low_checks["section_completeness"].score <= 2


def test_renormalization_on_partial_failure() -> None:
    outputs = {k: v for k, v in _ALL_OUTPUTS.items() if k != "ats"}

    result = calculate_scores(
        _STRONG_RESUME, _RAW_TEXT, outputs, failed_evaluators=["ats"]
    )

    assert result.methodology["ai_partial"] is True
    assert [c.category for c in result.ai_categories] != ["ats_compatibility"]
    assert "ats_compatibility" not in result.methodology["renormalized_weights"]

    # Renormalized weights must sum back to one whole.
    weights = result.methodology["renormalized_weights"]
    assert sum(weights.values()) == 1.0

    # ai_score equals the renormalized weighted average of surviving bands.
    expected = sum(c.weight * c.score for c in result.ai_categories) / sum(
        c.weight for c in result.ai_categories
    )
    assert result.ai_score == round(expected, 2)


def test_all_ai_failed_degrades_to_deterministic_only() -> None:
    result = calculate_scores(
        _STRONG_RESUME,
        _RAW_TEXT,
        {},
        failed_evaluators=[
            "recruiter",
            "ats",
            "technical",
            "content_quality",
        ],
    )

    assert result.ai_categories == []
    assert result.methodology["ai_partial"] is True
    assert result.overall_score == result.deterministic_score


def test_strong_resume_scores_higher_than_empty() -> None:
    strong = calculate_scores(_STRONG_RESUME, _RAW_TEXT, _ALL_OUTPUTS, [])
    empty = calculate_scores(_empty_resume(), "", _ALL_OUTPUTS, [])

    assert strong.overall_score > empty.overall_score
    assert 0 <= strong.overall_score <= 100
    assert 0 <= empty.overall_score <= 100
