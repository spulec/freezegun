import datetime
import fractions
import pytest
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from datetime import timedelta, tzinfo
from tests import utils
from typing import Any, Union


@freeze_time("2012-01-14")
def test_addition() -> None:
    now = datetime.datetime.now()
    later = now + datetime.timedelta(days=1)
    other_later = now + relativedelta(days=1)
    assert utils.is_fake_datetime(later)
    assert utils.is_fake_datetime(other_later)

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    other_tomorrow = today + relativedelta(days=1)
    assert utils.is_fake_date(tomorrow)
    assert utils.is_fake_date(other_tomorrow)


@freeze_time("2012-01-14")
def test_subtraction() -> None:
    now = datetime.datetime.now()
    before = now - datetime.timedelta(days=1)
    other_before = now - relativedelta(days=1)
    how_long = now - before
    assert utils.is_fake_datetime(before)
    assert utils.is_fake_datetime(other_before)
    assert isinstance(how_long, datetime.timedelta)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    other_yesterday = today - relativedelta(days=1)
    how_long = today - yesterday
    assert utils.is_fake_date(yesterday)
    assert utils.is_fake_date(other_yesterday)
    assert isinstance(how_long, datetime.timedelta)


@freeze_time("2012-01-14")
def test_datetime_timezone_none() -> None:
    now = datetime.datetime.now(tz=None)
    assert now == datetime.datetime(2012, 1, 14)


class GMT5(tzinfo):
    def utcoffset(self, dt: Any) -> timedelta:
        return timedelta(hours=5)

    def tzname(self, dt: Any) -> str:
        return "GMT +5"

    def dst(self, dt: Any) -> timedelta:
        return timedelta(0)


@freeze_time("2012-01-14 2:00:00")
def test_datetime_timezone_real() -> None:
    now = datetime.datetime.now(tz=GMT5())
    assert now == datetime.datetime(2012, 1, 14, 7, tzinfo=GMT5())
    assert now.utcoffset() == timedelta(0, 60 * 60 * 5)


@freeze_time("2012-01-14 2:00:00", tz_offset=-4)
def test_datetime_timezone_real_with_offset() -> None:
    now = datetime.datetime.now(tz=GMT5())
    assert now == datetime.datetime(2012, 1, 14, 3, tzinfo=GMT5())
    assert now.utcoffset() == timedelta(0, 60 * 60 * 5)


@freeze_time("2012-01-14 00:00:00")
def test_astimezone() -> None:
    now = datetime.datetime.now(tz=GMT5())
    converted = now.astimezone(GMT5())
    assert utils.is_fake_datetime(converted)


@freeze_time("2012-01-14 00:00:00")
def test_astimezone_tz_none() -> None:
    now = datetime.datetime.now(tz=GMT5())
    converted = now.astimezone()
    assert utils.is_fake_datetime(converted)


@freeze_time("2012-01-14 00:00:00")
def test_replace() -> None:
    now = datetime.datetime.now()
    modified_time = now.replace(year=2013)
    assert utils.is_fake_datetime(modified_time)

    today = datetime.date.today()
    modified_date = today.replace(year=2013)
    assert utils.is_fake_date(modified_date)


@freeze_time("Jan 14th, 2020", auto_tick_seconds=15)
def test_auto_tick() -> None:
    first_time = datetime.datetime.now()
    auto_incremented_time = datetime.datetime.now()
    assert first_time + datetime.timedelta(seconds=15) == auto_incremented_time


@pytest.mark.parametrize(
    "tick,expected_diff",
    (
        (datetime.timedelta(milliseconds=1500), 1.5),
        (1, 1),
        (1.5, 1.5),
        (fractions.Fraction(3, 2), 1.5),
    )
)
def test_auto_and_manual_tick(
    tick: Union[
        datetime.timedelta,
        int,
        float,
        # fractions.Fraction,
        # Fraction works at runtime, but not at type-checking time
        # cf. https://peps.python.org/pep-0484/#the-numeric-tower
    ],
    expected_diff: float
) -> None:
    first_time = datetime.datetime(2020, 1, 14, 0, 0, 0, 1)

    with freeze_time(first_time, auto_tick_seconds=2) as frozen_time:
        frozen_time.tick(tick)
        incremented_time = datetime.datetime.now()
        expected_time = first_time + datetime.timedelta(seconds=expected_diff)
        assert incremented_time == expected_time

        expected_time += datetime.timedelta(seconds=2)  # auto_tick_seconds

        frozen_time.tick(tick)
        incremented_time = datetime.datetime.now()
        expected_time += datetime.timedelta(seconds=expected_diff)
        assert incremented_time == expected_time
