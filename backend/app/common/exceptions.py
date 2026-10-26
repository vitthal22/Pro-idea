"""Custom application exceptions.

Every exception carries an HTTP status code and a machine-readable code so
the global handler in main.py can return structured JSON — never a raw
traceback.
"""

from typing import Any


class AppException(Exception):
    """Base exception for the application."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(AppException):
    """Raised when credentials are missing or invalid."""

    status_code = 401
    code = "UNAUTHORIZED"


class AuthorizationError(AppException):
    """Raised when the user lacks permission for the resource."""

    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppException):
    """Raised when business-level validation fails."""

    status_code = 400
    code = "VALIDATION_ERROR"


class ConflictError(AppException):
    """Raised when a resource already exists (e.g. duplicate email)."""

    status_code = 409
    code = "CONFLICT"


class InvalidFileError(AppException):
    """Raised when an uploaded file is invalid (type, size, content)."""

    status_code = 400
    code = "INVALID_FILE"


class ResumeParsingError(AppException):
    """Raised when resume text extraction fails."""

    status_code = 422
    code = "PARSING_FAILED"

    def __init__(self, reason: str, file_path: str) -> None:
        super().__init__(
            message=f"Could not parse resume: {reason}",
            details={"reason": reason, "file_path": file_path},
        )


class AIEvaluationError(AppException):
    """Raised when an AI evaluator fails after retries."""

    status_code = 502
    code = "AI_EVALUATION_FAILED"

    def __init__(self, evaluator: str, reason: str) -> None:
        super().__init__(
            message=f"Evaluator '{evaluator}' failed: {reason}",
            details={"evaluator": evaluator, "reason": reason},
        )


class AnalysisFailedError(AppException):
    """Raised when the analysis pipeline fails at a given stage."""

    status_code = 500
    code = "ANALYSIS_FAILED"

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(
            message=f"Analysis failed at stage '{stage}': {reason}",
            details={"stage": stage, "reason": reason},
        )
