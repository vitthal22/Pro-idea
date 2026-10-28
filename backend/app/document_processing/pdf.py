"""PDF text extraction (pdfplumber).

Synchronous by design: the caller runs it in a worker thread so the event
loop is never blocked by parsing.
"""

from pathlib import Path

import pdfplumber
from pdfminer.pdfexceptions import PDFException
from pdfplumber.utils.exceptions import PdfminerException

from app.common.exceptions import ResumeParsingError
from app.document_processing.cleaning import clean_extracted_text


def extract_pdf(file_path: Path) -> str:
    """Extract and clean text from every page of a PDF."""
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except (PDFException, OSError, ValueError, PdfminerException) as exc:
        raise ResumeParsingError(
            reason=f"pdf_read_error:{type(exc).__name__}",
            file_path=str(file_path),
        ) from exc
    return clean_extracted_text("\n".join(pages))
