"""Computes total years of experience from a resume's `Experience` entries.

Kept in Python rather than pushed into SQL: summing date-range durations
portably across Postgres and SQLite without dialect-specific date-arithmetic
functions is not straightforward, and this is only ever run against an
already-filtered, already-small candidate set (see
`ResumeRepository.find_all`'s `minimum_experience` handling), so the extra
round-trip cost is negligible. A simple additive sum is used — overlapping
date ranges are not de-duplicated, which is an accepted simplification.
"""

from datetime import date


def calculate_total_experience_years(
    entries: list[tuple[date | None, date | None]],
    *,
    as_of: date | None = None,
) -> float:
    """Sum the duration of each `(start_date, end_date)` pair, in years.

    Entries with no `start_date` are skipped (nothing to measure). A `None`
    `end_date` (an ongoing role) is treated as running through `as_of`
    (defaults to today).
    """
    reference_date = as_of or date.today()
    total_days = 0

    for start_date, end_date in entries:
        if start_date is None:
            continue
        effective_end = end_date or reference_date
        if effective_end <= start_date:
            continue
        total_days += (effective_end - start_date).days

    return round(total_days / 365.25, 2)
