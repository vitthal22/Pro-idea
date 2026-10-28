"""Heuristic quality gate for extracted resume text.

Pure and synchronous: no filesystem or network access, so it is cheap to
unit test and safe to run anywhere.
"""

from dataclasses import dataclass

MIN_WORDS = 100
MIN_PRINTABLE_RATIO = 0.6


@dataclass(frozen=True)
class TextQuality:
    """Result of checking extracted text for usability."""

    is_valid: bool
    word_count: int
    printable_ratio: float
    reason: str | None = None


def validate_text(text: str) -> TextQuality:
    """Check that text looks like a real resume, not an empty/garbled scan."""
    if not text.strip():
        return TextQuality(
            is_valid=False,
            word_count=0,
            printable_ratio=0.0,
            reason="empty_text",
        )

    printable_ratio = sum(
        1 for char in text if char.isprintable() or char.isspace()
    ) / len(text)
    word_count = len(text.split())

    if word_count < MIN_WORDS:
        return TextQuality(
            is_valid=False,
            word_count=word_count,
            printable_ratio=printable_ratio,
            reason=f"too_few_words:{word_count}",
        )
    if printable_ratio < MIN_PRINTABLE_RATIO:
        return TextQuality(
            is_valid=False,
            word_count=word_count,
            printable_ratio=printable_ratio,
            reason=f"garbled_text:{printable_ratio:.2f}",
        )
    return TextQuality(
        is_valid=True,
        word_count=word_count,
        printable_ratio=printable_ratio,
    )
