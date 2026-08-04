"""Skill detection via case-insensitive keyword matching against a predefined catalog."""

import re

from app.utils.skills import SKILLS


def _build_pattern() -> re.Pattern[str]:
    # Longest-first so multi-word/compound skills (e.g. "Spring Boot")
    # win over shorter overlapping ones (e.g. "Spring").
    escaped = sorted((re.escape(skill) for skill in SKILLS), key=len, reverse=True)
    return re.compile(rf"(?<!\w)(?:{'|'.join(escaped)})(?!\w)", re.IGNORECASE)


_SKILL_PATTERN = _build_pattern()
_CANONICAL_BY_LOWER = {skill.lower(): skill for skill in SKILLS}


def extract_skills(text: str) -> list[str]:
    """Return the sorted, deduplicated list of canonical skill names found in `text`."""
    found = {_CANONICAL_BY_LOWER[match.group().lower()] for match in _SKILL_PATTERN.finditer(text)}
    return sorted(found)
