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
    assert parse("coming Tues.", TODAY) == date(2025, 11, 25)


def test_last_weekday() -> None:
    assert parse("last Friday", TODAY) == date(2025, 11, 14)
    assert parse("previous Thurs", TODAY) == date(2025, 11, 13)


def test_this_weekday_allows_today() -> None:
    assert parse("this Thursday", TODAY) == TODAY


def test_month_name_absolute_dates() -> None:
    assert parse("December 1st, 2025", TODAY) == date(2025, 12, 1)
    assert parse("1 Dec 25", TODAY) == date(2025, 12, 1)
    assert parse("the 5th of May 2025", TODAY) == date(2025, 5, 5)
    assert parse("first of September 2025", TODAY) == date(2025, 9, 1)


def test_numeric_absolute_dates() -> None:
    assert parse("2025-12-01", TODAY) == date(2025, 12, 1)
    assert parse("2025/12/01", TODAY) == date(2025, 12, 1)
    assert parse("2025/12/04", TODAY) == date(2025, 12, 4)
    assert parse("12/1/2025", TODAY) == date(2025, 12, 1)


def test_month_arithmetic_clamps_to_last_valid_day() -> None:
    assert parse("1 month after January 31, 2024", TODAY) == date(2024, 2, 29)


def test_later_earlier_and_symbol_arithmetic() -> None:
    assert parse("3 days later", TODAY) == date(2025, 11, 23)
    assert parse("3 days earlier", TODAY) == date(2025, 11, 17)
    assert parse("tomorrow + 2 days", TODAY) == date(2025, 11, 23)


def test_first_and_last_day_of_relative_month() -> None:
    assert parse("first day of next month", TODAY) == date(2025, 12, 1)
    assert parse("last day of next month", TODAY) == date(2025, 12, 31)


def test_period_boundaries() -> None:
    assert parse("start of this week", TODAY) == date(2025, 11, 17)
    assert parse("end of this week", TODAY) == date(2025, 11, 23)
    assert parse("last day of next year", TODAY) == date(2026, 12, 31)
    assert parse("last day of 2025", TODAY) == date(2025, 12, 31)


def test_relative_month_names() -> None:
    assert parse("next January", TODAY) == date(2026, 1, 1)
    assert parse("next December 5th", TODAY) == date(2025, 12, 5)
    assert parse("last September", TODAY) == date(2025, 9, 1)


def test_unparseable_input_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        parse("hello world", TODAY)
    assert type(exc_info.value) is ValueError

    with pytest.raises(ValueError):
        parse("sometime after lunch", TODAY)
