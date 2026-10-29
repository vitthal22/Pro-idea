"""Hybrid scoring engine — deterministic checks (50%) + AI ratings (50%).

Implemented entirely in this module (ARCHITECTURE §13). Design rules:

- The AI never produces a raw number: evaluators return categorical
  ratings, and this module maps each rating to a fixed score band, so
  identical inputs + identical success/failure patterns → identical score.
- Mode weights live in ``MODE_WEIGHTS``; when an evaluator failed, its
  category is dropped and the surviving category weights renormalize.
  A failed evaluator is never scored as zero — silent zeros corrupt scores.
- If every AI evaluator failed, the overall score falls back to
  deterministic-only and ``methodology["ai_partial"]`` records it.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.schemas.report import (
    CategoryScore,
    DeterministicCheck,
    ScoringResult,
)
from app.schemas.resume import StructuredResume

# AI rating → deterministic midpoint of its score band (ARCHITECTURE §13:
# excellent 88-100, good 70-87, fair 45-69, poor 20-44, missing 0-19).
# AI rating → deterministic midpoint of its score band. v2 (2026-10-30)
# recalibrated to the 2026 hiring bar — the reference market scorecard:
# excellent 88, good 72, fair 50, poor 26, missing 5 (was 94/78.5/57/32/9.5,
# which let competent-but-generic resumes score in the high 70s).
_RATING_MIDPOINT: dict[str, float] = {
    "excellent": 88.0,
    "good": 72.0,
    "fair": 50.0,
    "poor": 26.0,
    "missing": 5.0,
}

# Score → the blunt verdict label shown on the scorecard.
_VERDICT_BANDS: list[tuple[float, str, str]] = [
    (
        80.0,
        "Interview-ready",
        "Strong by 2026 standards — the remaining gaps are fixable polish.",
    ),
    (
        65.0,
        "Needs work",
        "Real signals, but critical gaps will cost you interviews — fix the "
        "poison points first.",
    ),
    (
        45.0,
        "Will get screened out",
        "Generic and under-evidenced; automated filters and six-second "
        "scans will pass on this.",
    ),
    (
        0.0,
        "Instant-reject pile",
        "This reads as AI-generated filler with no verifiable specifics — "
        "rebuild before sending.",
    ),
]


def score_verdict(score: float) -> dict[str, str]:
    """Blunt verdict label + one-line explanation for a 0-100 score."""
    for threshold, label, line in _VERDICT_BANDS:
        if score >= threshold:
            return {"label": label, "line": line}
    label, line = _VERDICT_BANDS[-1][1], _VERDICT_BANDS[-1][2]
    return {"label": label, "line": line}


# First impression (strong/average/weak) stands in for the general mode's
# role-relevance category when the Job Matcher did not run.
_IMPRESSION_RATING: dict[str, str] = {
    "strong": "excellent",
    "average": "good",
    "weak": "poor",
}

# Category weights per mode (ARCHITECTURE §13, "Weights by Mode"). The AI
# side contributes 50% of the overall score, distributed by these weights.
MODE_WEIGHTS: dict[str, dict[str, float]] = {
    "general": {
        "content_quality": 0.25,
        "experience": 0.25,
        "skills_alignment": 0.15,
        "ats_compatibility": 0.20,
        "role_relevance": 0.15,
    },
    "role_based": {
        "content_quality": 0.20,
        "experience": 0.20,
        "skills_alignment": 0.20,
        "ats_compatibility": 0.15,
        "role_relevance": 0.25,
    },
    "jd_based": {
        "content_quality": 0.20,
        "experience": 0.20,
        "skills_alignment": 0.25,
        "ats_compatibility": 0.20,
        "role_relevance": 0.15,
    },
    # custom keeps the general weights; custom_instructions steer the
    # evaluators' focus instead of reweighting the outcome.
    "custom": {
        "content_quality": 0.25,
        "experience": 0.25,
        "skills_alignment": 0.15,
        "ats_compatibility": 0.20,
        "role_relevance": 0.15,
    },
}

# Which evaluator field feeds which scoring category. A category only
# scores when its source evaluator survived the run.
_CATEGORY_SOURCES: dict[str, tuple[str, str]] = {
    "content_quality": ("content_quality", "writing_quality_rating"),
    "experience": ("recruiter", "experience_relevance_rating"),
    "skills_alignment": ("technical", "technical_depth_rating"),
    "ats_compatibility": ("ats", "ats_readiness_rating"),
    "role_relevance": ("recruiter", "first_impression"),
}

# Bullets starting with one of these count as action-verb led.
_ACTION_VERBS = frozenset(
    """built led designed developed implemented managed created launched
    improved reduced increased optimized automated migrated mentored
    architected shipped delivered owned drove cut grew scaled maintained
    tested deployed refactored integrated streamlined established""".split()
)

_NUMBERS_RE = re.compile(r"\d")


def _check(name: str, score: float, max: float, details: str) -> DeterministicCheck:
    return DeterministicCheck(
        name=name, score=round(score, 2), max=max, details=details
    )


def _section_completeness(resume: StructuredResume) -> DeterministicCheck:
    sections = {
        "contact info": bool(resume.contact_info.email or resume.contact_info.name),
        "summary": bool(resume.professional_summary),
        "experience": bool(resume.experience),
        "education": bool(resume.education),
        "skills": bool(resume.skills),
    }
    present = sum(sections.values())
    missing = [name for name, ok in sections.items() if not ok]
    return _check(
        "section_completeness",
        present,
        5,
        f"{present}/5 standard sections present"
        + (f"; missing: {', '.join(missing)}" if missing else ""),
    )


def _bullet_points(resume: StructuredResume) -> DeterministicCheck:
    roles = len(resume.experience)
    bullets = sum(len(role.bullet_points) for role in resume.experience)
    if roles == 0:
        return _check("bullet_points", 0, 5, "No work-experience entries to score")
    avg = bullets / roles
    score = min(1.0, avg / 3) * 5  # 3+ bullets per role is the full mark
    return _check(
        "bullet_points",
        score,
        5,
        f"{bullets} bullets across {roles} roles (avg {avg:.1f}; full mark at 3+)",
    )


def _word_count(raw_text: str) -> DeterministicCheck:
    words = len(raw_text.split())
    if 300 <= words <= 900:
        score, band = 3.0, "in the ideal 300-900 range"
    elif 150 <= words < 300 or 900 < words <= 1200:
        score, band = 2.0, "slightly outside the ideal 300-900 range"
    elif words > 1200:
        score, band = 1.0, "bloated (over 1200 words)"
    else:
        score, band = 0.0, "too thin (under 150 words)"
    return _check("word_count", score, 3, f"{words} words — {band}")


def _contact_info(resume: StructuredResume) -> DeterministicCheck:
    score = (1.0 if resume.contact_info.email else 0.0) + (
        1.0 if resume.contact_info.phone else 0.0
    )
    missing = [
        channel
        for channel, present in (
            ("email", resume.contact_info.email),
            ("phone", resume.contact_info.phone),
        )
        if not present
    ]
    return _check(
        "contact_info",
        score,
        2,
        "email and phone present" if not missing else f"missing: {', '.join(missing)}",
    )


def _date_consistency(resume: StructuredResume) -> DeterministicCheck:
    if not resume.experience:
        return _check("date_consistency", 0, 3, "No work-experience entries to score")
    undated = sum(
        1 for role in resume.experience if not role.start_date and not role.is_current
    )
    score = max(0.0, 3.0 - undated)
    return _check(
        "date_consistency",
        score,
        3,
        "all roles dated"
        if undated == 0
        else f"{undated} role(s) with no start date and no 'current' marker",
    )


def _bullet_ratio_check(
    resume: StructuredResume,
    name: str,
    max_points: float,
    predicate,
    low_label: str,
    high_label: str,
) -> DeterministicCheck:
    bullets = [b for role in resume.experience for b in role.bullet_points]
    if not bullets:
        return _check(name, 0, max_points, "No bullets to score")
    hits = sum(1 for b in bullets if predicate(b))
    ratio = hits / len(bullets)
    return _check(
        name,
        ratio * max_points,
        max_points,
        f"{hits}/{len(bullets)} bullets {high_label}"
        if hits
        else f"0 bullets {low_label}",
    )


def _quantified_achievements(resume: StructuredResume) -> DeterministicCheck:
    return _bullet_ratio_check(
        resume,
        "quantified_achievements",
        5,
        lambda b: bool(_NUMBERS_RE.search(b)),
        "contain numbers",
        "contain numbers or metrics",
    )


def _action_verbs(resume: StructuredResume) -> DeterministicCheck:
    return _bullet_ratio_check(
        resume,
        "action_verbs",
        5,
        lambda b: b.split()[:1] and b.split()[0].lower() in _ACTION_VERBS,
        "start with an action verb",
        "start with an action verb",
    )


def _formatting_quality(raw_text: str) -> DeterministicCheck:
    if not raw_text:
        return _check("formatting_quality", 0, 5, "No extractable text")
    printable = sum(1 for ch in raw_text if ch.isprintable() or ch in "\n\r\t")
    ratio = printable / len(raw_text)
    return _check(
        "formatting_quality",
        ratio * 5,
        5,
        f"{ratio:.0%} printable characters from extraction",
    )


def _deterministic_checks(
    resume: StructuredResume, raw_text: str
) -> list[DeterministicCheck]:
    return [
        _section_completeness(resume),
        _bullet_points(resume),
        _word_count(raw_text),
        _contact_info(resume),
        _date_consistency(resume),
        _quantified_achievements(resume),
        _action_verbs(resume),
        _formatting_quality(raw_text),
    ]


def _rating_of(
    evaluator_name: str, field_name: str, outputs: dict[str, BaseModel]
) -> str | None:
    """Categorical rating from a surviving evaluator, or None if absent."""
    output = outputs.get(evaluator_name)
    value = getattr(output, field_name, None) if output is not None else None
    if isinstance(value, str):
        return value
    return None


def calculate_scores(
    resume: StructuredResume,
    raw_text: str,
    evaluator_outputs: dict[str, BaseModel],
    failed_evaluators: list[str],
    mode: str = "general",
) -> ScoringResult:
    """Hybrid score from deterministic checks and surviving AI ratings.

    Args:
        resume: AI-parsed resume the deterministic checks run on.
        raw_text: Extracted resume text (word count, printable ratio).
        evaluator_outputs: Surviving evaluator outputs (name → output).
        failed_evaluators: Names of evaluators that failed this run.
        mode: Analysis mode selecting the category weights.

    Returns:
        The full scoring result with breakdown and methodology.
    """
    checks = _deterministic_checks(resume, raw_text)
    det_total = sum(c.score for c in checks)
    det_max = sum(c.max for c in checks)
    det_score = round(det_total / det_max * 100, 2) if det_max else 0.0

    weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["general"])
    categories: list[CategoryScore] = []
    for category, weight in weights.items():
        if category == "role_relevance" and "job_matcher" in evaluator_outputs:
            # A real fit judgment beats the first-impression stand-in.
            source_eval, source_field = "job_matcher", "match_rating"
        else:
            source_eval, source_field = _CATEGORY_SOURCES[category]
        rating = _rating_of(source_eval, source_field, evaluator_outputs)
        if rating is None:
            continue
        if category == "role_relevance":
            if source_eval == "job_matcher":
                mapped = rating if rating in _RATING_MIDPOINT else "missing"
            else:
                # First impression mapped onto the quality scale.
                mapped = _IMPRESSION_RATING.get(rating, "poor")
        else:
            mapped = rating if rating in _RATING_MIDPOINT else "missing"
        categories.append(
            CategoryScore(
                category=category,
                rating=rating,
                score=_RATING_MIDPOINT[mapped],
                weight=weight,
                details=f"{source_eval}.{source_field}='{rating}' → band "
                f"'{mapped}' ({_RATING_MIDPOINT[mapped]}/100)",
            )
        )

    methodology: dict[str, object] = {
        "deterministic_weight": 0.5,
        "ai_weight": 0.5,
        "mode_weights": weights,
        "failed_evaluators": failed_evaluators,
        "ai_partial": False,
    }

    weight_sum = sum(c.weight for c in categories)
    if categories:
        # Renormalize: surviving categories' weights redistributed so the
        # AI side still sums to one whole.
        for scored in categories:
            scored.details += f"; renormalized weight {scored.weight / weight_sum:.3f}"
        ai_score = round(sum(c.weight * c.score for c in categories) / weight_sum, 2)
        if failed_evaluators:
            methodology["ai_partial"] = True
            methodology["renormalized_weights"] = {
                c.category: round(c.weight / weight_sum, 4) for c in categories
            }
        overall = round(0.5 * det_score + 0.5 * ai_score, 2)
    else:
        # Every AI evaluator failed — degrade to deterministic-only instead
        # of failing the analysis (resource rules: partial beats a 500).
        ai_score = 0.0
        methodology["ai_partial"] = True
        methodology["ai_side"] = "excluded: all AI evaluators failed"
        overall = round(det_score, 2)

    return ScoringResult(
        overall_score=overall,
        deterministic_checks=checks,
        deterministic_score=det_score,
        ai_categories=categories,
        ai_score=ai_score,
        methodology=methodology,
    )
