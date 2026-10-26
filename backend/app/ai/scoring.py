"""Analysis mode configurations - defines which evaluators run for each mode."""


from typing import Any

MODE_WEIGHTS: dict[str, dict[str, Any]] = {
    "general": {
        "name": "General Analysis",
        "description": "Full resume analysis across all categories",
        "evaluators": ["culture_fit"],
        "weights": {
            "culture_fit": 0.20,
        },
    },
    "role_based": {
        "name": "Role-Based Analysis",
        "description": "Resume analysis optimized for a specific job role",
        "evaluators": ["culture_fit"],
        "weights": {
            "culture_fit": 0.20,
        },
    },
    "jd_based": {
        "name": "Job Description-Based Analysis",
        "description": "Resume comparison against a specific job description",
        "evaluators": ["culture_fit"],
        "weights": {
            "culture_fit": 0.20,
        },
    },
    "custom": {
        "name": "Custom Analysis",
        "description": "User-provided focus areas for resume evaluation",
        "evaluators": ["culture_fit"],
        "weights": {
            "culture_fit": 0.20,
        },
    },
}


def get_mode_weight(mode: str, evaluator_type: str) -> float:
    """Get the weight for an evaluator type in a specific mode."""
    return MODE_WEIGHTS.get(mode, MODE_WEIGHTS["general"])["weights"].get(
        evaluator_type, 0.25
    )


def get_mode_evaluators(mode: str) -> list[str]:
    """Get evaluators for a specific mode."""
    return MODE_WEIGHTS.get(mode, MODE_WEIGHTS["general"])["evaluators"]