"""Application logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging with a consistent, structured format."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Third-party noise we do not need at INFO
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


app_logger = logging.getLogger("app")
