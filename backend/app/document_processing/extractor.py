"""Single entry point for resume text extraction.

Routes by MIME type, then applies the quality gate. OCR fallback for
image-only PDFs is a V2 feature (pytesseract + pdf2image); until then a
low-quality extraction fails cleanly with ``ResumeParsingError`` rather
than handing garbage to the AI pipeline.
"""

from dataclasses import dataclass
from pathlib import Path

from app.common.exceptions import ResumeParsingError
from app.document_processing.docx import extract_docx
from app.document_processing.pdf import extract_pdf
from app.document_processing.quality import TextQuality, validate_text

PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

_EXTRACTORS = {
    PDF_MIME_TYPE: extract_pdf,
    DOCX_MIME_TYPE: extract_docx,
}


@dataclass(frozen=True)
class ExtractedText:
    """Extraction result with the quality assessment that gated it."""

    raw_text: str
    extraction_method: str
    quality: TextQuality


def extract_text(file_path: Path, mime_type: str) -> ExtractedText:
    """Extract usable text from a resume file or raise ``ResumeParsingError``."""
    extractor = _EXTRACTORS.get(mime_type)
    if extractor is None:
        raise ResumeParsingError(
            reason=f"unsupported_mime_type:{mime_type}",
            file_path=str(file_path),
        )

    raw_text = extractor(file_path)
    quality = validate_text(raw_text)
    if not quality.is_valid:
        raise ResumeParsingError(
            reason=f"low_quality:{quality.reason}",
            file_path=str(file_path),
        )
    return ExtractedText(
        raw_text=raw_text,
        extraction_method=extractor.__name__,
        quality=quality,
    )
