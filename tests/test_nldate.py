from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 11, 20)  # Thursday


def test_today_tomorrow_and_yesterday() -> None:
    assert parse("today", TODAY) == TODAY
    assert parse("tomorrow", TODAY) == date(2025, 11, 21)
    assert parse("yesterday", TODAY) == date(2025, 11, 19)


def test_day_after_tomorrow() -> None:
    assert parse("the day after tomorrow", TODAY) == date(2025, 11, 22)


def test_duration_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025", TODAY) == date(2025, 11, 26)


def test_duration_after_relative_anchor() -> None:
    assert parse("1 year and 2 months after yesterday", TODAY) == date(2027, 1, 19)


def test_spelled_duration_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", TODAY) == date(2025, 12, 5)


def test_multiword_spelled_duration() -> None:
    assert parse("twenty one days after Nov 1, 2025", TODAY) == date(2025, 11, 22)


def test_couple_duration() -> None:
    assert parse("a couple of days from today", TODAY) == date(2025, 11, 22)


def test_in_duration() -> None:
    assert parse("in 3 days", TODAY) == date(2025, 11, 23)


def test_ago_duration() -> None:
    assert parse("10 weeks ago", TODAY) == date(2025, 9, 11)


def test_next_weekday() -> None:
    assert parse("next Tuesday", TODAY) == date(2025, 11, 25)


def test_last_weekday() -> None:
    assert parse("last Friday", TODAY) == date(2025, 11, 14)


def test_this_weekday_allows_today() -> None:
    assert parse("this Thursday", TODAY) == TODAY


def test_month_name_absolute_dates() -> None:
    assert parse("December 1st, 2025", TODAY) == date(2025, 12, 1)
    assert parse("1 Dec 25", TODAY) == date(2025, 12, 1)
    assert parse("the 5th of May 2025", TODAY) == date(2025, 5, 5)


def test_numeric_absolute_dates() -> None:
    assert parse("2025-12-01", TODAY) == date(2025, 12, 1)
    assert parse("12/1/2025", TODAY) == date(2025, 12, 1)


def test_month_arithmetic_clamps_to_last_valid_day() -> None:
    assert parse("1 month after January 31, 2024", TODAY) == date(2024, 2, 29)


def test_unparseable_input_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("sometime after lunch", TODAY)
