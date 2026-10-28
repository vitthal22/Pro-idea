"""Pydantic schemas for AI-parsed resume data.

These models are the contract between the AI parser and the rest of the
pipeline. Every field carries a ``Field(description=...)`` — descriptions
double as guidance inside the parser prompt, so write them as extraction
instructions.
"""

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact details found on the resume."""

    name: str | None = Field(None, description="Full name exactly as written")
    email: str | None = Field(None, description="Email address, or null if absent")
    phone: str | None = Field(None, description="Phone number, or null if absent")
    location: str | None = Field(
        None, description="City/region line, or null if absent"
    )
    linkedin_url: str | None = Field(
        None, description="LinkedIn profile URL, or null if absent"
    )
    github_url: str | None = Field(
        None, description="GitHub profile URL, or null if absent"
    )
    portfolio_url: str | None = Field(
        None, description="Personal site/portfolio URL, or null if absent"
    )


class ExperienceItem(BaseModel):
    """One role in the work-experience section."""

    job_title: str = Field(description="Job title as written")
    company: str | None = Field(None, description="Company or employer name")
    location: str | None = Field(None, description="Job location, or null")
    start_date: str | None = Field(
        None, description="Start date exactly as written, e.g. 'Jan 2022'"
    )
    end_date: str | None = Field(
        None,
        description="End date as written, or null when the role is current",
    )
    is_current: bool = Field(
        False, description="True when the resume marks this job as ongoing"
    )
    bullet_points: list[str] = Field(
        default_factory=list,
        description="Achievement bullets under this role, one string each",
    )


class EducationItem(BaseModel):
    """One entry in the education section."""

    degree: str = Field(description="Degree or qualification as written")
    institution: str | None = Field(None, description="School or university")
    field_of_study: str | None = Field(None, description="Major/specialisation")
    graduation_date: str | None = Field(
        None, description="Graduation date as written, or null"
    )


class ProjectItem(BaseModel):
    """One personal or academic project."""

    name: str = Field(description="Project name")
    description: str | None = Field(None, description="One-line description")
    technologies: list[str] = Field(
        default_factory=list, description="Languages, frameworks, tools used"
    )


class CertificationItem(BaseModel):
    """One certification or license."""

    name: str = Field(description="Certification name")
    issuer: str | None = Field(None, description="Issuing organisation")
    date_issued: str | None = Field(None, description="Issue date as written")


class StructuredResume(BaseModel):
    """Structured extraction of a resume's content.

    The parser fills this from raw resume text. Anything the resume does
    not mention stays null/empty — never invent values.
    """

    contact_info: ContactInfo = Field(
        default_factory=ContactInfo,
        description="Name and contact details from the header",
    )
    professional_summary: str | None = Field(
        None, description="Summary/objective paragraph, or null if absent"
    )
    total_years_experience: float | None = Field(
        None,
        ge=0,
        description="Total professional experience in years, only when the "
        "resume states it; null otherwise",
    )
    experience: list[ExperienceItem] = Field(
        default_factory=list, description="Work experience, most recent first"
    )
    education: list[EducationItem] = Field(
        default_factory=list, description="Education entries"
    )
    skills: list[str] = Field(
        default_factory=list, description="All listed skills and technologies"
    )
    certifications: list[CertificationItem] = Field(
        default_factory=list, description="Certifications and licenses"
    )
    projects: list[ProjectItem] = Field(
        default_factory=list, description="Projects listed on the resume"
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Human languages the candidate knows (not programming)",
    )
