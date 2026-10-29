"""Pydantic schemas for AI evaluator outputs.

The AI never returns raw numbers — every quality judgment is a categorical
rating (ARCHITECTURE §13), and the scoring engine maps ratings to fixed
score ranges deterministically. Every field carries
``Field(description=...)``; descriptions double as guidance inside the
evaluator prompts, so write them as review instructions.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Universal quality scale. "missing" means the resume gives no evidence at
# all — scoring treats it as the lowest band, never as a failure.
QualityRating = Literal["excellent", "good", "fair", "poor", "missing"]


class RecruiterEvaluatorOutput(BaseModel):
    """Six-second-recruiter screen of the resume."""

    summary: str = Field(
        max_length=300, description="Two-sentence verdict a recruiter would give"
    )
    first_impression: Literal["strong", "average", "weak"] = Field(
        description="Gut reaction after a six-second scan"
    )
    first_impression_reason: str = Field(
        max_length=300, description="Why the scan landed there — cite the resume"
    )
    experience_relevance_rating: QualityRating = Field(
        description="How relevant and recent the work experience is"
    )
    experience_relevance_findings: list[str] = Field(
        default_factory=list,
        description="Specific observations backing the experience rating",
    )
    credibility_rating: Literal["high", "medium", "low"] = Field(
        description="How believable the claims are (specifics vs vague buzzwords)"
    )
    credibility_flags: list[str] = Field(
        default_factory=list,
        description="Claims that raise doubt (unexplained gaps, title inflation, "
        "buzzword walls)",
    )
    red_flags: list[str] = Field(
        default_factory=list,
        description="Deal-breakers a recruiter would hold against the candidate",
    )
    would_shortlist: bool = Field(
        description="True if a recruiter would advance this resume to the next round"
    )
    would_shortlist_reason: str = Field(
        max_length=300, description="The single deciding factor"
    )


class ATSEvaluatorOutput(BaseModel):
    """Applicant-tracking-system readability of the resume."""

    summary: str = Field(
        max_length=300, description="How an ATS parse of this resume would fare"
    )
    ats_readiness_rating: QualityRating = Field(
        description="Chance the resume survives automated parsing and ranking"
    )
    formatting_issues: list[str] = Field(
        default_factory=list,
        description="Layout choices that break or confuse ATS parsers (tables, "
        "columns, graphics, unusual headers)",
    )
    missing_keywords: list[str] = Field(
        default_factory=list,
        description="Common keywords for the candidate's evident profession that "
        "the resume never mentions",
    )


class TechnicalEvaluatorOutput(BaseModel):
    """Technical credibility and depth of the resume."""

    summary: str = Field(
        max_length=300, description="Technical verdict in two sentences"
    )
    technical_depth_rating: QualityRating = Field(
        description="Depth of real technical work evidenced (projects, metrics, "
        "specifics) versus claimed skills"
    )
    identified_stack: list[str] = Field(
        default_factory=list,
        description="Languages, frameworks, and tools the resume actually "
        "evidences through work or projects (not just skill lists)",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Claimed skills with no supporting evidence, or critical "
        "skills missing for the evident role",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Technically impressive, well-evidenced items worth keeping",
    )


class ContentQualityEvaluatorOutput(BaseModel):
    """Writing quality of the resume."""

    summary: str = Field(
        max_length=300, description="Writing-quality verdict in two sentences"
    )
    writing_quality_rating: QualityRating = Field(
        description="Overall prose quality: clarity, conciseness, tone"
    )
    generic_language_issues: list[str] = Field(
        default_factory=list,
        description="Clichés, filler, and interchangeable phrasing "
        "(quote the offending text)",
    )
    quantification_rating: QualityRating = Field(
        description="How well achievements are backed by numbers and metrics"
    )
    clarity_findings: list[str] = Field(
        default_factory=list,
        description="Confusing, contradictory, or buried information with where "
        "it occurs",
    )
