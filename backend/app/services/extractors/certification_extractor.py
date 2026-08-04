"""Certification entry extraction from the resume's CERTIFICATIONS section."""

import re
from datetime import date
from typing import TypedDict

from app.utils.date_utils import find_date

_SEPARATOR_PATTERN = re.compile(r"\s*[|–—-]\s*")
_TRAILING_YEAR_PATTERN = re.compile(r",?\s*\b(19|20)\d{2}\b")


class CertificationEntry(TypedDict):
    name: str | None
    issuer: str | None
    date: date | None


def extract_certifications(section_text: str) -> list[CertificationEntry]:
    entries: list[CertificationEntry] = []

    for raw_line in section_text.splitlines():
        line = raw_line.strip(" \t-•*")
        if not line:
            continue

        date_value = find_date(line)
        cleaned = _TRAILING_YEAR_PATTERN.sub("", line) if date_value else line

        parts = [part.strip() for part in _SEPARATOR_PATTERN.split(cleaned) if part.strip()]
        name = parts[0] if parts else None
        issuer = parts[1] if len(parts) > 1 else None

        entries.append(CertificationEntry(name=name, issuer=issuer, date=date_value))

    return entries
