"""Extraction of name, email, phone, and address from resume text."""

import re

from app.core.logger import get_logger

logger = get_logger(__name__)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

_PHONE_CANDIDATE_PATTERN = re.compile(r"\+?\d[\d .()-]{7,16}\d")

_URL_HINT_PATTERN = re.compile(
    r"(https?://|www\.|linkedin\.com|github\.com|\.com|\.io|\.dev|\.net)", re.IGNORECASE
)

# A short, title-cased line of 2-4 words (e.g. "John Smith") — the
# conventional position/shape of a name at the top of a resume.
_NAME_LINE_PATTERN = re.compile(r"^[A-Z][a-zA-Z.'-]*(?:\s+[A-Z][a-zA-Z.'-]*){1,3}$")

_spacy_nlp = None
_spacy_load_attempted = False


def _get_spacy_model():
    """Lazily load spaCy's small English model, caching the result across calls.

    If the model isn't installed (e.g. `en_core_web_sm` wasn't downloaded),
    this logs a warning once and returns `None` — name extraction then
    relies solely on the heuristic in `extract_name`, so parsing never
    hard-fails because of a missing NLP model.
    """
    global _spacy_nlp, _spacy_load_attempted
    if _spacy_load_attempted:
        return _spacy_nlp

    _spacy_load_attempted = True
    try:
        import spacy

        _spacy_nlp = spacy.load("en_core_web_sm")
    except Exception:
        logger.warning(
            "spaCy model 'en_core_web_sm' is unavailable; falling back to "
            "heuristic-only name extraction."
        )
        _spacy_nlp = None
    return _spacy_nlp


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group() if match else None


def extract_phone(text: str) -> str | None:
    """Find the first digit run that plausibly looks like a phone number.

    Heuristic, not a full phone-number grammar: any candidate span whose
    digit count falls in [10, 15] is accepted. This intentionally accepts
    a range of formats (e.g. `+91 9876543210`, `(123) 456-7890`) at the
    cost of occasionally matching a long non-phone digit run.
    """
    for match in _PHONE_CANDIDATE_PATTERN.finditer(text):
        candidate = match.group().strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 15:
            return candidate
    return None


def extract_name(header_text: str) -> str | None:
    """Best-effort name extraction from the resume's header block.

    Tries a positional heuristic first — a short, title-cased line with
    no digits/@/URL near the top of the resume — then falls back to
    spaCy's PERSON named-entity recognition over the header text.
    """
    for line in header_text.splitlines()[:6]:
        candidate = line.strip()
        if not candidate or len(candidate) > 60:
            continue
        if "@" in candidate or _URL_HINT_PATTERN.search(candidate):
            continue
        if any(char.isdigit() for char in candidate):
            continue
        if _NAME_LINE_PATTERN.match(candidate):
            return candidate

    nlp = _get_spacy_model()
    if nlp is None:
        return None

    doc = nlp(header_text[:500])
    for entity in doc.ents:
        if entity.label_ == "PERSON":
            return entity.text.strip()
    return None


def extract_address(header_text: str) -> str | None:
    """Best-effort address heuristic.

    Looks for a header line containing a comma and digits (street
    number/ZIP) but with fewer than 10 digits total, to avoid picking up
    the phone number line. There is no reliable regex-only way to
    distinguish a real address from other comma-separated header text,
    so this deliberately stays conservative.
    """
    for line in header_text.splitlines():
        candidate = line.strip()
        if not candidate or "@" in candidate or _URL_HINT_PATTERN.search(candidate):
            continue
        if "," not in candidate or not any(char.isdigit() for char in candidate):
            continue
        digits = re.sub(r"\D", "", candidate)
        if len(digits) < 10:
            return candidate
    return None
