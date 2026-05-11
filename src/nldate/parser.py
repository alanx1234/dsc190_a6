"""A small parser for common natural-language date expressions."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta


class DateParseError(ValueError):
    """Raised when a natural-language date cannot be parsed."""


@dataclass(frozen=True)
class Duration:
    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0

    def apply_to(self, anchor: date, sign: int = 1) -> date:
        shifted = _add_months(anchor, sign * (self.years * 12 + self.months))
        return shifted + timedelta(days=sign * (self.weeks * 7 + self.days))


MONTHS: dict[str, int] = {
    month.lower(): index for index, month in enumerate(calendar.month_name) if month
}
MONTHS.update({
    month.lower(): index for index, month in enumerate(calendar.month_abbr) if month
})

WEEKDAYS: dict[str, int] = {
    day.lower(): index for index, day in enumerate(calendar.day_name)
}
WEEKDAYS.update({
    day.lower(): index for index, day in enumerate(calendar.day_abbr)
})

NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "couple": 2,
}

UNITS = {
    "day": "days",
    "days": "days",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
}

_MONTH_PATTERN = "|".join(
    sorted((re.escape(name) for name in MONTHS), key=len, reverse=True),
)
_WEEKDAY_PATTERN = "|".join(
    sorted((re.escape(name) for name in WEEKDAYS), key=len, reverse=True),
)
_ORDINAL_SUFFIX_RE = re.compile(r"\b(\d+)(st|nd|rd|th)\b")
_WHITESPACE_RE = re.compile(r"\s+")


def parse(s: str, today: date | None = None) -> date:
    """Parse a common English date expression into a ``datetime.date``.

    Args:
        s: Natural-language date text.
        today: Reference date for relative expressions. Defaults to today's date.

    Raises:
        ValueError: If the expression is empty or unsupported.
    """
    reference = today if today is not None else date.today()
    text = _normalize(s)
    if not text:
        msg = "date expression must not be empty"
        raise DateParseError(msg)
    return _parse_expression(text, reference)


def _parse_expression(text: str, today: date) -> date:
    text = _strip_outer_noise(text)

    relative = _parse_relative_expression(text, today)
    if relative is not None:
        return relative

    weekday = _parse_weekday_expression(text, today)
    if weekday is not None:
        return weekday

    absolute = _parse_absolute_date(text, today)
    if absolute is not None:
        return absolute

    msg = f"could not parse date expression: {text!r}"
    raise DateParseError(msg)


def _parse_relative_expression(text: str, today: date) -> date | None:
    direct = {
        "today": today,
        "now": today,
        "tomorrow": today + timedelta(days=1),
        "yesterday": today - timedelta(days=1),
        "day after tomorrow": today + timedelta(days=2),
        "the day after tomorrow": today + timedelta(days=2),
        "day before yesterday": today - timedelta(days=2),
        "the day before yesterday": today - timedelta(days=2),
    }
    if text in direct:
        return direct[text]

    if match := re.fullmatch(r"in (.+)", text):
        return _parse_duration(match.group(1)).apply_to(today)

    if match := re.fullmatch(r"(.+) ago", text):
        return _parse_duration(match.group(1)).apply_to(today, sign=-1)

    if match := re.fullmatch(r"(.+) (?:from|after) now", text):
        return _parse_duration(match.group(1)).apply_to(today)

    if match := re.fullmatch(r"(.+) (?:from|after) today", text):
        return _parse_duration(match.group(1)).apply_to(today)

    if match := re.fullmatch(r"(.+) before today", text):
        return _parse_duration(match.group(1)).apply_to(today, sign=-1)

    if match := re.fullmatch(r"(.+) (before|after|from) (.+)", text):
        amount, direction, anchor_text = match.groups()
        duration = _try_parse_duration(amount)
        if duration is not None:
            anchor = _parse_expression(anchor_text, today)
            sign = -1 if direction == "before" else 1
            return duration.apply_to(anchor, sign=sign)

    if match := re.fullmatch(r"(.+) (plus|minus) (.+)", text):
        anchor_text, direction, amount = match.groups()
        anchor = _parse_expression(anchor_text, today)
        sign = -1 if direction == "minus" else 1
        return _parse_duration(amount).apply_to(anchor, sign=sign)

    if match := re.fullmatch(r"(next|last) (day|week|month|year)", text):
        direction, unit = match.groups()
        sign = 1 if direction == "next" else -1
        return Duration(**{f"{unit}s": 1}).apply_to(today, sign=sign)

    return None


def _parse_weekday_expression(text: str, today: date) -> date | None:
    if match := re.fullmatch(rf"(next|last|this) ({_WEEKDAY_PATTERN})", text):
        modifier, weekday_name = match.groups()
        target = WEEKDAYS[weekday_name]
        if modifier == "next":
            days = (target - today.weekday()) % 7
            return today + timedelta(days=days or 7)
        if modifier == "last":
            days = (today.weekday() - target) % 7
            return today - timedelta(days=days or 7)
        return today + timedelta(days=(target - today.weekday()) % 7)

    if text in WEEKDAYS:
        target = WEEKDAYS[text]
        return today + timedelta(days=(target - today.weekday()) % 7)

    return None


def _parse_absolute_date(text: str, today: date) -> date | None:
    if text == "new years day":
        return date(today.year, 1, 1)
    if text == "christmas":
        return date(today.year, 12, 25)

    month_day_year = re.fullmatch(
        rf"({_MONTH_PATTERN}) (\d{{1,2}})(?: (\d{{2,4}}))?",
        text,
    )
    if month_day_year:
        month_name, day_text, year_text = month_day_year.groups()
        year = _coerce_year(year_text, today.year)
        return date(year, MONTHS[month_name], int(day_text))

    day_month_year = re.fullmatch(
        rf"(\d{{1,2}}) ({_MONTH_PATTERN})(?: (\d{{2,4}}))?",
        text,
    )
    if day_month_year:
        day_text, month_name, year_text = day_month_year.groups()
        year = _coerce_year(year_text, today.year)
        return date(year, MONTHS[month_name], int(day_text))

    day_of_month_year = re.fullmatch(
        rf"(?:the )?(\d{{1,2}}) of ({_MONTH_PATTERN})(?: (\d{{2,4}}))?",
        text,
    )
    if day_of_month_year:
        day_text, month_name, year_text = day_of_month_year.groups()
        year = _coerce_year(year_text, today.year)
        return date(year, MONTHS[month_name], int(day_text))

    month_year = re.fullmatch(rf"({_MONTH_PATTERN}) (\d{{2,4}})", text)
    if month_year:
        month_name, year_text = month_year.groups()
        return date(_coerce_year(year_text, today.year), MONTHS[month_name], 1)

    iso = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso:
        year_text, month_text, day_text = iso.groups()
        return date(int(year_text), int(month_text), int(day_text))

    slash_or_dash = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", text)
    if slash_or_dash:
        month_text, day_text, year_text = slash_or_dash.groups()
        year = _coerce_year(year_text, today.year)
        return date(year, int(month_text), int(day_text))

    return None


def _parse_duration(text: str) -> Duration:
    duration = _try_parse_duration(text)
    if duration is None:
        msg = f"could not parse duration: {text!r}"
        raise DateParseError(msg)
    return duration


def _try_parse_duration(text: str) -> Duration | None:
    cleaned = _normalize(text)
    cleaned = re.sub(r"\b(and|of|the)\b", " ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return None

    parts = cleaned.split()
    totals = {"years": 0, "months": 0, "weeks": 0, "days": 0}
    index = 0
    matched = False
    while index < len(parts):
        amount, next_index = _consume_number(parts, index)
        if amount is None or next_index >= len(parts):
            return None
        unit = UNITS.get(parts[next_index])
        if unit is None:
            return None
        totals[unit] += amount
        matched = True
        index = next_index + 1

    if not matched:
        return None
    return Duration(**totals)


def _consume_number(parts: list[str], start: int) -> tuple[int | None, int]:
    token = parts[start]
    if token.isdigit() or "-" in token:
        parsed_token = _parse_number_token(token)
        return parsed_token, start + 1

    if token == "a" and start + 1 < len(parts) and parts[start + 1] == "couple":
        return 2, start + 2

    total = 0
    index = start
    consumed = False
    while index < len(parts):
        value = NUMBER_WORDS.get(parts[index])
        if value is None:
            break
        total += value
        consumed = True
        index += 1

    if not consumed:
        return None, start
    return total, index


def _parse_number_token(token: str) -> int | None:
    if token.isdigit():
        return int(token)
    if "-" in token:
        total = 0
        for part in token.split("-"):
            value = NUMBER_WORDS.get(part)
            if value is None:
                return None
            total += value
        return total
    return NUMBER_WORDS.get(token)


def _add_months(anchor: date, months: int) -> date:
    month_index = anchor.month - 1 + months
    year = anchor.year + month_index // 12
    month = month_index % 12 + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _coerce_year(year_text: str | None, default: int) -> int:
    if year_text is None:
        return default
    year = int(year_text)
    if year < 100:
        return 2000 + year
    return year


def _normalize(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace(",", " ")
    normalized = normalized.replace(".", " ")
    normalized = normalized.replace("'", "")
    normalized = _ORDINAL_SUFFIX_RE.sub(r"\1", normalized)
    normalized = normalized.replace("weeks'", "weeks")
    normalized = normalized.replace("week's", "weeks")
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def _strip_outer_noise(text: str) -> str:
    for prefix in ("on ", "by ", "at "):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text
