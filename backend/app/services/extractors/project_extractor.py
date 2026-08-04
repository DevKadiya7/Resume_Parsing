"""Project entry extraction from the resume's PROJECTS section."""

import re
from typing import TypedDict

from app.services.extractors.skill_extractor import extract_skills

_TECHNOLOGIES_LINE_PATTERN = re.compile(
    r"^(?:Technologies|Tech Stack|Tools|Built with)\s*[:\-]\s*(.+)$", re.IGNORECASE
)


class ProjectEntry(TypedDict):
    name: str | None
    description: str | None
    technologies: str | None


def _split_blocks(section_text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", section_text) if block.strip()]
    if blocks:
        return blocks
    return [section_text.strip()] if section_text.strip() else []


def extract_projects(section_text: str) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []

    for block in _split_blocks(section_text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        name = lines[0]
        technologies: str | None = None
        description_lines: list[str] = []

        for line in lines[1:]:
            tech_match = _TECHNOLOGIES_LINE_PATTERN.match(line)
            if tech_match:
                technologies = tech_match.group(1).strip()
            else:
                description_lines.append(line)

        if technologies is None:
            # Fall back to reusing the skill catalog to tag technologies
            # mentioned in the project description, rather than a second
            # independent keyword list.
            matched_skills = extract_skills(block)
            technologies = ", ".join(matched_skills) if matched_skills else None

        entries.append(
            ProjectEntry(
                name=name,
                description="\n".join(description_lines).strip() or None,
                technologies=technologies,
            )
        )

    return entries
