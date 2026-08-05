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

# Section-heading words that must never be accepted as a person's name,
# however confidently a positional/NER heuristic proposes them — a resume
# with no blank line before "Skills"/"Machine Learning"/etc. can otherwise
# fool a purely shape-based check.
_HEADING_BLOCKLIST = frozenset(
    {
        "skills",
        "technical skills",
        "core competencies",
        "machine learning",
        "education",
        "academic background",
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "projects",
        "personal projects",
        "academic projects",
        "portfolio",
        "certifications",
        "certificates",
        "licenses",
        "summary",
        "professional summary",
        "profile",
        "objective",
        "about me",
        "achievements",
        "hobbies",
        "interests",
        "references",
        "social links",
        "links",
        "contact",
        "contact information",
        "area of interest",
    }
)

# "Frontend: React.js, HTML5, ..." / "Skills: Python, ..." — a label
# followed by a colon and a comma-separated list is a strong signal of a
# skills/details bullet, never an address.
_LABELLED_LINE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z /&]{1,30}:\s*\S")

_ADDRESS_KEYWORD_PATTERN = re.compile(
    r"\b(street|st\.|road|rd\.|avenue|ave\.|lane|ln\.|nagar|sector|colony|apartment|apt\.|"
    r"house\s*no\.?|block|society|district|dist\.|pin\s*code|zip\s*code|p\.?o\.?\s*box)\b",
    re.IGNORECASE,
)
# "City, State 12345" / "City, Country" — a plausible "<place>, <place>" shape.
_CITY_STATE_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z .]{1,30},\s*[A-Za-z][A-Za-z .]{1,30}(\s*-?\s*\d{4,6})?$"
)

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


def _is_heading_like(candidate: str) -> bool:
    return candidate.strip().lower().rstrip(":").strip() in _HEADING_BLOCKLIST


def _looks_like_contact_line(candidate: str) -> bool:
    return bool("@" in candidate or _PHONE_CANDIDATE_PATTERN.search(candidate))


def extract_name(header_text: str, prominent_line: str | None = None) -> str | None:
    """Best-effort name extraction from the resume's header block.

    Tries, in order:
    1. `prominent_line` — the largest-font-size line near the top of page
       1 (see `text_extractor.extract_prominent_top_line`), if it's
       plausibly a name. This is the strongest available signal (a
       resume's name is conventionally its largest text) and is checked
       before any positional/shape heuristic, per design intent: don't
       just grab the first heading-shaped line.
    2. A positional heuristic — a short, title-cased line with no
       digits/@/URL, scanned only through the lines *before* the first
       line that looks like contact info (email/phone) — a name never
       appears after that point.
    3. spaCy's PERSON named-entity recognition, scoped to that same
       pre-contact-info text rather than the whole header block, so a
       table or paragraph further down can't be mistaken for a name.

    A candidate that matches a known section-heading word (e.g. "Skills",
    "Machine Learning") is rejected at every stage.
    """
    if prominent_line:
        candidate = prominent_line.strip()
        if (
            candidate
            and len(candidate) <= 60
            and not _looks_like_contact_line(candidate)
            and not _URL_HINT_PATTERN.search(candidate)
            and not _is_heading_like(candidate)
        ):
            return candidate

    lines_before_contact: list[str] = []
    for line in header_text.splitlines()[:8]:
        candidate = line.strip()
        if not candidate:
            continue
        if _looks_like_contact_line(candidate):
            break  # a name never appears after the contact-info line
        lines_before_contact.append(candidate)

    for candidate in lines_before_contact:
        if len(candidate) > 60 or _URL_HINT_PATTERN.search(candidate):
            continue
        if _is_heading_like(candidate):
            continue
        if _NAME_LINE_PATTERN.match(candidate):
            return candidate

    nlp = _get_spacy_model()
    if nlp is None or not lines_before_contact:
        return None

    doc = nlp("\n".join(lines_before_contact)[:500])
    for entity in doc.ents:
        if entity.label_ != "PERSON":
            continue
        candidate = entity.text.strip()
        if candidate and not _is_heading_like(candidate):
            return candidate
    return None


def extract_address(header_text: str) -> str | None:
    """Best-effort address heuristic.

    Only accepts a line that (a) isn't a "Label: value" style bullet
    (skills/details lines like "Frontend: React.js, HTML5, ..." are
    rejected outright) and (b) contains either a recognizable address
    keyword (Street/Road/Nagar/Sector/...) or a "City, State/Country
    [ZIP]"-shaped fragment. There is no reliable regex-only way to
    identify an address with certainty, so this stays conservative and
    returns `None` rather than guessing when nothing matches.
    """
    for line in header_text.splitlines():
        candidate = line.strip()
        if not candidate or "@" in candidate or _URL_HINT_PATTERN.search(candidate):
            continue
        if _LABELLED_LINE_PATTERN.match(candidate):
            continue
        if _ADDRESS_KEYWORD_PATTERN.search(candidate) or _CITY_STATE_PATTERN.match(candidate):
            digits = re.sub(r"\D", "", candidate)
            if len(digits) <= 12:  # excludes a phone-number line slipping through
                return candidate
    return None
