import datetime
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from datetime import timedelta, tzinfo
from tests import utils


@freeze_time("2012-01-14")
def test_addition():
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
def test_subtraction():
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
def test_datetime_timezone_none():
    now = datetime.datetime.now(tz=None)
    assert now == datetime.datetime(2012, 1, 14)


class GMT5(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=5)

    def tzname(self, dt):
        return "GMT +5"

    def dst(self, dt):
        return timedelta(0)


@freeze_time("2012-01-14 2:00:00")
def test_datetime_timezone_real():
    now = datetime.datetime.now(tz=GMT5())
    assert now == datetime.datetime(2012, 1, 14, 7, tzinfo=GMT5())
    assert now.utcoffset() == timedelta(0, 60 * 60 * 5)


@freeze_time("2012-01-14 2:00:00", tz_offset=-4)
def test_datetime_timezone_real_with_offset():
    now = datetime.datetime.now(tz=GMT5())
    assert now == datetime.datetime(2012, 1, 14, 3, tzinfo=GMT5())
    assert now.utcoffset() == timedelta(0, 60 * 60 * 5)


@freeze_time("2012-01-14 00:00:00")
def test_astimezone():
    now = datetime.datetime.now(tz=GMT5())
    converted = now.astimezone(GMT5())
    assert utils.is_fake_datetime(converted)


@freeze_time("2012-01-14 00:00:00")
def test_astimezone_tz_none():
    now = datetime.datetime.now(tz=GMT5())
    converted = now.astimezone()
    assert utils.is_fake_datetime(converted)


@freeze_time("2012-01-14 00:00:00")
def test_replace():
    now = datetime.datetime.now()
    modified_time = now.replace(year=2013)
    assert utils.is_fake_datetime(modified_time)

    today = datetime.date.today()
    modified_date = today.replace(year=2013)
    assert utils.is_fake_date(modified_date)
