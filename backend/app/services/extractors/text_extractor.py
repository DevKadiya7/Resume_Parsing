"""PDF text extraction via PyMuPDF, plus text-cleaning helpers."""

import re

import fitz  # PyMuPDF

from app.exceptions.custom_exceptions import (
    CorruptedPdfException,
    EmptyPdfException,
    EncryptedPdfException,
)

_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_WHITESPACE = re.compile(r"[ \t]+\n")
_MULTI_SPACES = re.compile(r"[ \t]{2,}")


def extract_text(pdf_bytes: bytes) -> str:
    """Open `pdf_bytes` with PyMuPDF and return its cleaned, page-ordered text.

    Raises `EncryptedPdfException` if the PDF is password-protected and
    cannot be authenticated with an empty password, `CorruptedPdfException`
    if it cannot be opened/read at all, and `EmptyPdfException` if no
    extractable text is found on any page.
    """
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise CorruptedPdfException("The uploaded PDF is corrupted and cannot be read.") from exc

    try:
        if document.is_encrypted and not document.authenticate(""):
            raise EncryptedPdfException(
                "The uploaded PDF is password-protected and cannot be parsed."
            )

        if document.page_count == 0:
            raise EmptyPdfException("The uploaded PDF contains no pages.")

        pages_text = [page.get_text("text") for page in document]
    finally:
        document.close()

    cleaned = clean_text("\n".join(pages_text))
    if not cleaned.strip():
        raise EmptyPdfException("The uploaded PDF contains no extractable text.")

    return cleaned


def clean_text(text: str) -> str:
    """Normalize line endings/whitespace and collapse duplicate blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WHITESPACE.sub("\n", text)
    text = _MULTI_SPACES.sub(" ", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)
    return text.strip()
