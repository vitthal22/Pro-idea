"""Pydantic schemas for AI evaluator outputs."""

from pydantic import BaseModel, Field


class EvaluatorOutput(BaseModel):
    """Base output schema for all AI evaluators."""

    summary: str = Field(description="Overall evaluation summary")
    critical_issues: list[str] = Field(
        default_factory=list, description="Critical issues found"
    )
    strengths: list[str] = Field(
        default_factory=list, description="Key strengths identified"
    )


class RecruiterEvaluatorOutput(EvaluatorOutput):
    """Output schema for the Recruiter evaluator."""

    model_config = {"from_attributes": True}

    overall_score: int = Field(
        ge=0, le=100, description="Recruiter rating score (0-100)"
    )
    hiring_likelihood: str = Field(
        description="Hiring likelihood category",
        pattern="^(High|Medium|Low)$",
    )
    resume_format_assessment: str = Field(
        description="Assessment of resume format effectiveness",
        pattern="^(Strong|Acceptable|Weak)$",
    )


class ATSEvaluatorOutput(EvaluatorOutput):
    """Output schema for the ATS evaluator."""

    model_config = {"from_attributes": True}

    ats_compatibility_score: int = Field(
        ge=0, le=100, description="ATS compatibility score (0-100)"
    )
    missing_keywords: list[str] = Field(
        default_factory=list, description="Keywords missing from resume"
    )
    formatting_issues: list[str] = Field(
        default_factory=list, description="ATS formatting issues"
    )


class TechnicalEvaluatorOutput(EvaluatorOutput):
    """Output schema for the Technical evaluator."""

    model_config = {"from_attributes": True}

    technical_score: int = Field(
        ge=0, le=100, description="Technical competence score (0-100)"
    )
    languages: list[str] = Field(
        default_factory=list, description="Programming languages identified"
    )
    frameworks: list[str] = Field(
        default_factory=list, description="Frameworks and tools identified"
    )


class ContentQualityEvaluatorOutput(EvaluatorOutput):
    """Output schema for the Content Quality evaluator."""

    model_config = {"from_attributes": True}

    content_score: int = Field(
        ge=0, le=100, description="Content quality score (0-100)"
    )
    readability_grade: str = Field(
        description="Readability grade level",
        pattern="^(A|B|C|D|F)$",
    )
    writing_clarity: str = Field(
        description="Writing clarity assessment",
        pattern="^(Clear|SomewhatClear|Unclear)$",
    )