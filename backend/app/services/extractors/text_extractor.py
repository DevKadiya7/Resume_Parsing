"""PDF text extraction via PyMuPDF, plus text-cleaning helpers.

Two things beyond plain `page.get_text("text")` turned out to matter for
real-world resumes (see the module docstrings on `section_splitter` and
`social_extractor` for how each is consumed):

1. Many resumes exported from Google Docs/Canva/etc. embed invisible
   zero-width formatting characters (U+200B, U+200C, U+FEFF, ...) after
   words — including section headings. Left in place, they silently break
   *every* exact string comparison downstream (`"projects<ZWSP>" !=
   "projects"`), which is exactly the kind of bug that only shows up on
   real documents, never on hand-written test fixtures. They're stripped
   here, once, at the source.
2. A resume's real LinkedIn/GitHub/portfolio links are frequently attached
   as clickable hyperlink *annotations* on anchor text like "LinkedIn" —
   the URL itself never appears in the visible text layer at all. Those
   annotations are pulled out via `extract_hyperlink_uris()`, kept
   deliberately separate from `extract_text()`'s return value (which
   drives section splitting), and merged in by `ParserService` only for
   the one extractor that needs them — `social_extractor`. Appending them
   directly onto the sectioned text would attach them to whatever the
   *last* detected section happens to be, corrupting it.
"""

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

# Zero-width space/non-joiner/joiner, BOM/zero-width no-break space, word
# joiner, soft hyphen — invisible in a viewer, present in the text layer of
# many resume exports (Google Docs in particular). Stripped outright
# rather than treated as whitespace, since collapsing them to a space
# could wrongly split a word in two (e.g. a ZWNJ inside a ligature).
# Written as explicit `\uXXXX` escapes so there's no ambiguity about which
# invisible codepoint is being matched.
_INVISIBLE_CHARS = re.compile("[​‌‍﻿⁠­]")
# Non-breaking space behaves like a normal space for our purposes (word
# boundaries, header matching) but isn't matched by `\s` in all contexts.
_NBSP = re.compile(" ")


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


def extract_hyperlink_uris(pdf_bytes: bytes) -> list[str]:
    """Collect external URI hyperlink targets from every page's link annotations.

    A resume's "LinkedIn"/"GitHub" header entries are frequently just
    anchor text with the real URL attached as a clickable link annotation,
    invisible to `get_text()`. `mailto:` links are skipped — the email
    address is already found directly in the visible text by
    `contact_extractor`, and including a raw `mailto:` URI here would just
    be noise for `social_extractor`. Best-effort: returns `[]` if the PDF
    can't be opened rather than raising, since by the time this runs
    `extract_text()` has already succeeded on the same bytes.
    """
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return []

    try:
        uris: list[str] = []
        seen: set[str] = set()
        for page in document:
            for link in page.get_links():
                uri = link.get("uri")
                if not uri or uri.lower().startswith("mailto:"):
                    continue
                if uri not in seen:
                    seen.add(uri)
                    uris.append(uri)
        return uris
    finally:
        document.close()


def clean_text(text: str) -> str:
    """Normalize line endings/whitespace, strip invisible characters, and
    collapse duplicate blank lines.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _INVISIBLE_CHARS.sub("", text)
    text = _NBSP.sub(" ", text)
    text = _TRAILING_WHITESPACE.sub("\n", text)
    text = _MULTI_SPACES.sub(" ", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def extract_prominent_top_line(pdf_bytes: bytes) -> str | None:
    """Return the largest-font-size line of text near the top of page 1.

    A resume's name is conventionally set in the largest font on the page,
    which is a much stronger signal than "looks like a title-cased line"
    when the ordinary heuristic in `contact_extractor.extract_name` can't
    find a confident match (e.g. an invisible character broke the regex,
    or the name is styled/positioned unusually). Best-effort: returns
    `None` on any structural surprise rather than raising, since this is
    only ever used as one input among several to name detection.
    """
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return None

    try:
        if document.page_count == 0:
            return None
        page = document[0]
        page_height = page.rect.height
        top_cutoff = page_height * 0.35  # only consider the top third-ish of the page

        best_text: str | None = None
        best_size = 0.0
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                if line["bbox"][1] > top_cutoff:
                    continue
                for span in line.get("spans", []):
                    candidate = span.get("text", "").strip()
                    size = span.get("size", 0.0)
                    if candidate and size > best_size:
                        best_size = size
                        best_text = candidate
        return _INVISIBLE_CHARS.sub("", best_text).strip() if best_text else None
    except Exception:
        return None
    finally:
        document.close()
