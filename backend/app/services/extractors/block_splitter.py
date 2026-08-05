"""Splits a resume section's text into per-entry blocks.

Shared by the education/experience/project extractors (previously each
had its own near-identical, blank-line-only splitter — duplicated logic
this module replaces).
"""

import re

BULLET_PREFIX_PATTERN = re.compile(r"^\s*[•\-*‣●▪◦○]\s*")


def split_entry_blocks(section_text: str) -> list[str]:
    """Split `section_text` into one string per entry.

    Blank-line separation is tried first — the clean, common case. Many
    real resumes instead pack multiple bullet-prefixed entries back to
    back with *no* blank line between them (e.g. "• Project One ...\\n•
    Project Two ..."); when blank-line splitting collapses everything into
    a single block but the text actually contains two or more
    bullet-prefixed lines, it's re-split on each bullet line instead,
    since that's the real entry boundary in that layout.
    """
    blank_line_blocks = [
        block.strip() for block in re.split(r"\n\s*\n", section_text) if block.strip()
    ]

    bullet_line_count = sum(
        1 for line in section_text.splitlines() if BULLET_PREFIX_PATTERN.match(line)
    )
    if len(blank_line_blocks) <= 1 and bullet_line_count >= 2:
        blocks: list[str] = []
        current: list[str] = []
        for line in section_text.splitlines():
            if BULLET_PREFIX_PATTERN.match(line) and current:
                blocks.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append("\n".join(current).strip())
        return [block for block in blocks if block.strip()]

    if blank_line_blocks:
        return blank_line_blocks

    return [section_text.strip()] if section_text.strip() else []


def strip_bullet_prefix(line: str) -> str:
    """Remove a leading bullet marker (and the whitespace after it) from one line."""
    return BULLET_PREFIX_PATTERN.sub("", line).strip()
