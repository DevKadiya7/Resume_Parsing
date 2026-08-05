"""Splits cleaned resume text into named sections by detecting header lines."""

_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "objective", "about me"),
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "skills & tools",
        "languages",
        "frameworks",
        "libraries",
    ),
    "education": (
        "education",
        "academic background",
        "educational qualifications",
        "academic qualification",
        "qualification",
        "qualifications",
        "degrees",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "employment",
        "internship",
        "internships",
        "freelance",
    ),
    "projects": ("projects", "personal projects", "academic projects", "portfolio"),
    "certifications": (
        "certifications",
        "certificates",
        "licenses & certifications",
        "licenses and certifications",
        "licenses",
        "license",
        "training",
        "trainings",
    ),
    "social_links": ("social links", "links", "profiles"),
    # Recognized purely as section *boundaries*, not extracted by anything
    # — without this, a trailing "Achievements"/"Hobbies"/etc. block (none
    # of which map to a schema field) would otherwise keep being read as
    # part of whatever the previous real section was (most often
    # "experience", since it's commonly the section right before these).
    "other": (
        "achievements",
        "accomplishments",
        "awards",
        "hobbies",
        "interests",
        "area of interest",
        "references",
        "declaration",
        "personal details",
    ),
}

_HEADER_LOOKUP: dict[str, str] = {
    alias: section for section, aliases in _SECTION_ALIASES.items() for alias in aliases
}
# Longest alias first, so e.g. "work experience" is tried before the
# shorter "experience" would otherwise mask it in the fuzzy prefix check.
_ALIASES_BY_LENGTH = sorted(_HEADER_LOOKUP.items(), key=lambda pair: len(pair[0]), reverse=True)

_MAX_HEADER_LENGTH = 45
_HEADING_SEPARATORS = (" ", "&", "/", "-", ",")


def _looks_like_heading(line: str) -> bool:
    """Heading lines are short and don't trail off like a sentence."""
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_HEADER_LENGTH:
        return False
    return not stripped.endswith((".", ",", ";"))


def _match_section(line: str) -> str | None:
    """Identify whether `line` is a section-header line, and if so, which section.

    Two passes:
    1. Exact match (ignoring case and a trailing colon) against a known
       alias — precise, and the common case.
    2. A fuzzy prefix match for headings that tack on extra words beyond a
       known alias (e.g. "Work Experience & Internship", "Certifications
       & Licenses") — only attempted for short, heading-shaped lines, and
       only when the alias is followed by a natural separator (not
       mid-word), to keep ordinary prose that happens to start a sentence
       with "Experience..." or "Skills..." from being misread as a new
       section boundary.
    """
    normalized = line.strip().rstrip(":").strip().lower()
    if not normalized or len(normalized) > _MAX_HEADER_LENGTH:
        return None

    exact = _HEADER_LOOKUP.get(normalized)
    if exact is not None:
        return exact

    if not _looks_like_heading(line):
        return None

    for alias, section in _ALIASES_BY_LENGTH:
        if not normalized.startswith(alias):
            continue
        remainder = normalized[len(alias) :].strip()
        if not remainder or normalized[len(alias) : len(alias) + 1] in _HEADING_SEPARATORS:
            return section

    return None


def split_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections.

    Lines before the first recognized header live under the `"header"`
    key (name/contact info). A line counts as a header if it matches a
    known section alias — either exactly, or as a heading-shaped line
    that *starts with* an alias (see `_match_section`) — which keeps
    prose that merely mentions e.g. "skills" mid-sentence from being
    misread as a section boundary while still tolerating headings like
    "Work Experience & Internship" that a strict exact match would miss.
    """
    sections: dict[str, list[str]] = {"header": []}
    current = "header"

    for line in text.split("\n"):
        section = _match_section(line)
        if section is not None:
            current = section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}
