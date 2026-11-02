"""Text extraction and quality-gate tests."""

from pathlib import Path

import pytest

from app.common.exceptions import ResumeParsingError
from app.document_processing.extractor import (
    DOCX_MIME_TYPE,
    PDF_MIME_TYPE,
    extract_text,
)
from app.document_processing.quality import validate_text

LONG_RESUME = " ".join(f"skill{i}" for i in range(130))


def test_validate_text_accepts_a_real_resume() -> None:
    quality = validate_text(f"Senior Python developer. {LONG_RESUME}")

    assert quality.is_valid
    assert quality.word_count >= 100
    assert quality.printable_ratio == 1.0
    assert quality.reason is None


def test_validate_text_rejects_empty_short_and_garbled() -> None:
    assert validate_text("   ").reason == "empty_text"

    short = validate_text("Only a few words here")
    assert not short.is_valid
    assert short.reason is not None and short.reason.startswith("too_few_words")

    garbled = validate_text(("\x00\x01 " * 200).strip())
    assert not garbled.is_valid
    assert garbled.reason is not None and garbled.reason.startswith("garbled_text")


def test_extract_pdf_returns_page_text(
    tmp_path: Path,
    pdf_bytes_factory,
) -> None:
    path = tmp_path / "cv.pdf"
    path.write_bytes(pdf_bytes_factory(f"Senior engineer {LONG_RESUME}"))

    result = extract_text(path, PDF_MIME_TYPE)

    assert result.extraction_method == "extract_pdf"
    assert "Senior engineer" in result.raw_text
    assert result.quality.is_valid


def test_extract_docx_preserves_order_and_tables(
    tmp_path: Path,
    docx_bytes_factory,
) -> None:
    path = tmp_path / "cv.docx"
    path.write_bytes(docx_bytes_factory(f"Backend developer {LONG_RESUME}"))

    result = extract_text(path, DOCX_MIME_TYPE)

    assert result.extraction_method == "extract_docx"
    assert result.raw_text.startswith("Experience")
    assert "Python | 8 years" in result.raw_text
    assert result.quality.word_count > 100


def test_unsupported_mime_type_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "cv.txt"
    path.write_text("hello")

    with pytest.raises(ResumeParsingError) as exc:
        extract_text(path, "text/plain")

    assert "unsupported_mime_type" in exc.value.details["reason"]


def test_low_quality_text_is_rejected(
    tmp_path: Path,
    pdf_bytes_factory,
) -> None:
    path = tmp_path / "short.pdf"
    path.write_bytes(pdf_bytes_factory("short"))

    with pytest.raises(ResumeParsingError) as exc:
        extract_text(path, PDF_MIME_TYPE)

    assert exc.value.details["reason"].startswith("low_quality")


def test_broken_docx_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "broken.docx"
    path.write_bytes(b"definitely not a docx")

    with pytest.raises(ResumeParsingError) as exc:
        extract_text(path, DOCX_MIME_TYPE)

    assert exc.value.code == "PARSING_FAILED"
    assert exc.value.details["reason"].startswith("docx_read_error")
