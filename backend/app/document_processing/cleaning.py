"""Whitespace cleanup shared by every extractor."""


def clean_extracted_text(text: str) -> str:
    """Collapse runs of whitespace and drop empty lines.

    Word wrapping in PDFs produces ragged lines; normalizing each line keeps
    the text readable without destroying paragraph breaks.
    """
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)
