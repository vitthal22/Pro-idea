"""DOCX text extraction (python-docx).

Paragraphs and tables are read in document order so a resume's section
layout survives extraction. Synchronous by design — callers thread it.
"""

from collections.abc import Iterator
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentObject
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.common.exceptions import ResumeParsingError
from app.document_processing.cleaning import clean_extracted_text


def _iter_blocks(document: DocumentObject) -> Iterator[Paragraph | Table]:
    """Yield paragraphs and tables in their real document order."""
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def extract_docx(file_path: Path) -> str:
    """Extract and clean text from a .docx file."""
    try:
        document = Document(str(file_path))
        parts: list[str] = []
        for block in _iter_blocks(document):
            if isinstance(block, Paragraph):
                if block.text.strip():
                    parts.append(block.text)
            else:
                for row in block.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    if any(cells):
                        parts.append(" | ".join(cells))
    except (PackageNotFoundError, KeyError, OSError, ValueError) as exc:
        raise ResumeParsingError(
            reason=f"docx_read_error:{type(exc).__name__}",
            file_path=str(file_path),
        ) from exc
    return clean_extracted_text("\n".join(parts))
