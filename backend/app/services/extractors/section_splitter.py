"""Splits cleaned resume text into named sections by detecting header lines."""

_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "objective", "about me"),
    "skills": ("skills", "technical skills", "core competencies", "skills & tools"),
    "education": ("education", "academic background", "educational qualifications"),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
    ),
    "projects": ("projects", "personal projects", "academic projects"),
    "certifications": (
        "certifications",
        "certificates",
        "licenses & certifications",
        "licenses and certifications",
    ),
    "social_links": ("social links", "links", "profiles"),
}

_HEADER_LOOKUP: dict[str, str] = {
    alias: section for section, aliases in _SECTION_ALIASES.items() for alias in aliases
}


def _match_section(line: str) -> str | None:
    normalized = line.strip().rstrip(":").strip().lower()
    if not normalized or len(normalized) > 40:
        return None
    return _HEADER_LOOKUP.get(normalized)


def split_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections.

    Lines before the first recognized header live under the `"header"`
    key (name/contact info). A line counts as a header only if it
    *entirely* matches one of the known aliases (ignoring case and a
    trailing colon) — this keeps prose that merely mentions e.g. "skills"
    mid-sentence from being misread as a section boundary.
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
