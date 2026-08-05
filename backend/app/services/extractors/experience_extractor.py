"""Work experience entry extraction from the resume's EXPERIENCE section."""

import re
from datetime import date
from typing import TypedDict

from app.services.extractors.block_splitter import split_entry_blocks, strip_bullet_prefix
from app.utils.date_utils import DATE_RANGE_PATTERN, parse_date_range

_LOCATION_PATTERN = re.compile(r"\b([A-Z][a-zA-Z.\s]+,\s*[A-Z]{2,}(?:\s*\d{5})?|Remote)\b")
# " - " / " | " use a plain hyphen; " – " / " — " cover en/em dashes, which
# several real resumes use as the title/company separator instead.
_HEADER_SEPARATORS = (" at ", " @ ", " | ", " - ", " – ", " — ", ", ")


class ExperienceEntry(TypedDict):
    company: str | None
    job_title: str | None
    location: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    description: str | None


def _split_title_company(line: str) -> tuple[str | None, str | None]:
    for separator in _HEADER_SEPARATORS:
        if separator in line:
            left, right = line.split(separator, 1)
            return (left.strip() or None), (right.strip() or None)
    return (line.strip() or None), None


def extract_experience(section_text: str) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []

    for block in split_entry_blocks(section_text):
        lines = [strip_bullet_prefix(line) for line in block.splitlines() if line.strip()]
        lines = [line for line in lines if line]
        if not lines:
            continue

        header_index = next(
            (
                i
                for i, line in enumerate(lines)
                if DATE_RANGE_PATTERN.search(line) is None
                and any(sep in line for sep in _HEADER_SEPARATORS)
            ),
            0,
        )
        job_title, company = _split_title_company(lines[header_index])

        start_date, end_date, is_current = parse_date_range(block)

        location_match = _LOCATION_PATTERN.search(block)
        location = location_match.group(1).strip() if location_match else None

        description_lines = [
            line
            for i, line in enumerate(lines)
            if i != header_index and not DATE_RANGE_PATTERN.search(line) and line != location
        ]
        description = "\n".join(description_lines).strip() or None

        if not any([job_title, company]):
            continue

        entries.append(
            ExperienceEntry(
                company=company,
                job_title=job_title,
                location=location,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                description=description,
            )
        )

    return entries
