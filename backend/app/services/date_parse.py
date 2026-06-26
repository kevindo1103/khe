"""Date/duration parsing helpers for obligation derivation.

Returns None for non-parseable input (D-08: never fabricate).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Tuple

# 2024-06-19, 2024/06/19, 19/06/2024, 19-06-2024, 19/6/2024
_ISO_RE = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$")
_DMY_RE = re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$")

# "ngày 19 tháng 6 năm 2024" / "Ngày 19 tháng 06 năm 2024"
_VIETNAMESE_DATE_RE = re.compile(
    r"(?:ngày|Ngày)\s+(\d{1,2})\s+(?:tháng|Tháng)\s+(\d{1,2})\s+(?:năm|Năm)\s+(\d{4})",
    re.IGNORECASE,
)

# 12 tháng, 12 thang, 12 months, 12m
_MONTHS_RE = re.compile(r"(\d+)\s*(?:tháng|thang|months|month|m)", re.IGNORECASE)

# 2 năm, 2 nam, 2 years, 2y
_YEARS_RE = re.compile(r"(\d+)\s*(?:năm|nam|years|year|y)", re.IGNORECASE)

# "vô thời hạn" / "không thời hạn" / "không xác định"
_OPEN_ENDED_RE = re.compile(r"vô thời hạn|không thời hạn|không xác định|open ended", re.IGNORECASE)


def parse_date(value: str | None) -> datetime | None:
    """Parse a Vietnamese/Vietnamese-style date string to a datetime.

    Returns None if the value cannot be parsed.
    """
    if not value or not value.strip():
        return None
    value = value.strip()

    if match := _ISO_RE.match(value):
        year, month, day = match.groups()
        return _to_datetime(int(year), int(month), int(day))

    if match := _DMY_RE.match(value):
        day, month, year = match.groups()
        return _to_datetime(int(year), int(month), int(day))

    if match := _VIETNAMESE_DATE_RE.search(value):
        day, month, year = match.groups()
        return _to_datetime(int(year), int(month), int(day))

    return None


def _to_datetime(year: int, month: int, day: int) -> datetime | None:
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def parse_duration_months(value: str | None) -> int | None:
    """Parse a duration string into a number of months.

    Returns None for non-numeric or open-ended durations.
    """
    if not value or not value.strip():
        return None
    value = value.strip()

    if _OPEN_ENDED_RE.search(value):
        return None

    # Years first (more specific than months if both present).
    if match := _YEARS_RE.search(value):
        return int(match.group(1)) * 12

    if match := _MONTHS_RE.search(value):
        return int(match.group(1))

    # Bare number → treat as months if it looks like a duration context.
    if re.match(r"^\d+$", value):
        return int(value)

    return None


def add_months(start: datetime, months: int) -> datetime:
    """Add months to a datetime, clamping day to the end of month if needed."""
    total_months = start.year * 12 + (start.month - 1) + months
    new_year = total_months // 12
    new_month = total_months % 12 + 1
    max_day = _days_in_month(new_year, new_month)
    new_day = min(start.day, max_day)
    return datetime(new_year, new_month, new_day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def parse_date_or_duration(
    value: str | None,
) -> Tuple[datetime | None, int | None]:
    """Try to parse a value as either a date or a duration.

    Returns (date, None) if it's a date, (None, months) if it's a duration,
    or (None, None) if neither.
    """
    date = parse_date(value)
    if date is not None:
        return date, None
    months = parse_duration_months(value)
    if months is not None:
        return None, months
    return None, None
