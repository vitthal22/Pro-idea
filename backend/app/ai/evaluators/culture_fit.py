"""Culture Fit evaluator — recruiter-lens evaluation of the resume."""

from typing import Any

from app.ai.prompts.evaluators.culture_fit import SYSTEM_PROMPT
from app.ai.provider import call_ai
from app.common.exceptions import AIEvaluationError
from app.schemas.evaluators import RecruiterEvaluatorOutput


async def run_culture_fit_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the culture fit evaluator on resume data.

    Args:
        resume_data: Parsed resume information.
        context: Additional context (e.g. company values, team profile).

    Returns:
        dict with the evaluator output.

    Raises:
        AIEvaluationError: If the AI call fails or the output does not
            validate against the evaluator schema.
    """
    user_prompt = (
        "Evaluate this resume for culture fit:\n\n"
        f"RESUME DATA:\n{resume_data}\n\n"
        "Provide an evaluation focused on culture fit alignment."
    )

    result = await call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=RecruiterEvaluatorOutput,
    )

    evaluation = result.data
    if not isinstance(evaluation, RecruiterEvaluatorOutput):
        raise AIEvaluationError(
            evaluator="culture_fit",
            reason="model returned no structured evaluation",
        )

    return {
        "summary": evaluation.summary,
        "critical_issues": evaluation.critical_issues,
        "strengths": evaluation.strengths,
        "overall_score": evaluation.overall_score,
        "hiring_likelihood": evaluation.hiring_likelihood,
        "resume_format_assessment": evaluation.resume_format_assessment,
    }
