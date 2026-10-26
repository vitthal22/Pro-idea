"""Culture Fit evaluator for resume analysis."""

from typing import Any

from app.ai.provider import call_ai

from app.ai.prompts.evaluators.culture_fit import SYSTEM_PROMPT


async def run_culture_fit_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the culture fit evaluator on resume data.

    Args:
        resume_data: Parsed resume information
        context: Additional context (e.g., company values, team profile)

    Returns:
        dict with evaluator output
    """
    user_prompt = f"""Evaluate this resume for culture fit:

    RESUME DATA:
    {resume_data}

    Provide evaluation focused on culture fit alignment."""
    
    raw_response = await call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
    
    result = {
        "summary": raw_response.get("summary", "Culture fit evaluation completed"),
        "critical_issues": raw_response.get("critical_issues", []),
        "strengths": raw_response.get("strengths", []),
        "overall_score": raw_response.get("overall_score", 50),
        "hiring_likelihood": raw_response.get("hiring_likelihood", "Medium"),
        "resume_format_assessment": raw_response.get(
            "resume_format_assessment", "Acceptable"
        ),
    }
    
    return result