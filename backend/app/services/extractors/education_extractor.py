"""Education entry extraction from the resume's EDUCATION section."""

import re
from datetime import date
from typing import TypedDict

from app.utils.date_utils import parse_date_range

_DEGREE_PATTERN = re.compile(
    r"\b(Bachelor(?:'s)?(?: of [A-Za-z]+)?|Master(?:'s)?(?: of [A-Za-z]+)?|"
    r"B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|BCA|MCA|MBA|B\.?Sc|M\.?Sc|"
    r"Ph\.?D\.?|Diploma|Associate(?:'s)?)\b",
    re.IGNORECASE,
)
_INSTITUTION_KEYWORDS_PATTERN = re.compile(
    r"\b(University|College|Institute|School|Academy)\b", re.IGNORECASE
)
_GRADE_PATTERN = re.compile(
    r"(?:CGPA|GPA|Percentage|Grade)\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:%|/\s*\d+(?:\.\d+)?)?)",
    re.IGNORECASE,
)


class EducationEntry(TypedDict):
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_date: date | None
    end_date: date | None
    grade: str | None


def _split_blocks(section_text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", section_text) if block.strip()]
    if blocks:
        return blocks
    return [section_text.strip()] if section_text.strip() else []


def _extract_degree_and_field(block: str) -> tuple[str | None, str | None]:
    for line in block.splitlines():
        match = _DEGREE_PATTERN.search(line)
        if not match:
            continue
        degree = match.group(1)
        remainder = line[match.end() :].strip()
        remainder = re.sub(r"^(?:in|of)\s+", "", remainder, flags=re.IGNORECASE).strip(" ,-")
        return degree, (remainder or None)
    return None, None


def _extract_institution(block: str) -> str | None:
    for line in block.splitlines():
        stripped = line.strip()
        if stripped and _INSTITUTION_KEYWORDS_PATTERN.search(stripped):
            return stripped
    return None


def extract_education(section_text: str) -> list[EducationEntry]:
    entries: list[EducationEntry] = []

    for block in _split_blocks(section_text):
        degree, field_of_study = _extract_degree_and_field(block)
        institution = _extract_institution(block)
        start_date, end_date, _ = parse_date_range(block)

        grade_match = _GRADE_PATTERN.search(block)
        grade = grade_match.group(1).strip() if grade_match else None

        if not any([degree, institution, field_of_study]):
            continue

        entries.append(
            EducationEntry(
                institution=institution,
                degree=degree,
                field_of_study=field_of_study,
                start_date=start_date,
                end_date=end_date,
                grade=grade,
            )
        )

    return entries
