"""Date-range parsing shared by the education and experience extractors.

Centralized here so both extractors handle "Jan 2020 - Present",
"2019 - 2021", "03/2021 - 08/2022", etc. identically instead of each
reimplementing date parsing.
"""

import re
from datetime import date

import dateparser

_MONTH_TOKEN = r"[A-Za-z]{3,9}\.?\s+\d{4}"
_NUMERIC_TOKEN = r"\d{1,2}/\d{4}"
_YEAR_TOKEN = r"\d{4}"
_CURRENT_TOKEN = r"[Pp]resent|[Cc]urrent|[Oo]ngoing|[Nn]ow"

_START_TOKEN = rf"(?:{_MONTH_TOKEN}|{_NUMERIC_TOKEN}|{_YEAR_TOKEN})"
_END_TOKEN = rf"(?:{_MONTH_TOKEN}|{_NUMERIC_TOKEN}|{_YEAR_TOKEN}|{_CURRENT_TOKEN})"

DATE_RANGE_PATTERN = re.compile(
    rf"(?P<start>{_START_TOKEN})\s*(?:-|–|—|to)\s*(?P<end>{_END_TOKEN})"
)

_CURRENT_PATTERN = re.compile(_CURRENT_TOKEN)
_YEAR_ONLY_PATTERN = re.compile(rf"^{_YEAR_TOKEN}$")
_SINGLE_DATE_PATTERN = re.compile(_START_TOKEN)


def _parse_single_date(token: str) -> date | None:
    token = token.strip()
    if not token:
        return None
    if _YEAR_ONLY_PATTERN.match(token):
        return date(int(token), 1, 1)
    parsed = dateparser.parse(token, settings={"PREFER_DAY_OF_MONTH": "first"})
    return parsed.date() if parsed else None


def parse_date_range(text: str) -> tuple[date | None, date | None, bool]:
    """Find and parse the first date range in `text`.

    Returns `(start_date, end_date, is_current)`. If no range is found,
    returns `(None, None, False)`. If the end token is "Present"/
    "Current"/etc., `end_date` is `None` and `is_current` is `True`.
    """
    match = DATE_RANGE_PATTERN.search(text)
    if not match:
        return None, None, False

    start_date = _parse_single_date(match.group("start"))
    end_raw = match.group("end")

    if _CURRENT_PATTERN.fullmatch(end_raw.strip()):
        return start_date, None, True

    return start_date, _parse_single_date(end_raw), False


def find_date(text: str) -> date | None:
    """Find and parse the first standalone date-like token in `text`.

    For single-date fields (e.g. a certification's issue date), as
    opposed to `parse_date_range`'s start/end pair.
    """
    match = _SINGLE_DATE_PATTERN.search(text)
    if not match:
        return None
    return _parse_single_date(match.group())
