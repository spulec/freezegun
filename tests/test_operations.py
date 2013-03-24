import datetime
import sure
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from datetime import timedelta, tzinfo


@freeze_time("2012-01-14")
def test_addition():
    now = datetime.datetime.now()
    later = now + datetime.timedelta(days=1)
    other_later = now + relativedelta(days=1)
    assert isinstance(later, datetime.datetime)
    assert isinstance(other_later, datetime.datetime)

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    other_tomorrow = today + relativedelta(days=1)
    assert isinstance(tomorrow, datetime.date)
    assert isinstance(other_tomorrow, datetime.date)


@freeze_time("2012-01-14")
def test_subtraction():
    now = datetime.datetime.now()
    before = now - datetime.timedelta(days=1)
    other_before = now - relativedelta(days=1)
    how_long = now - before
    assert isinstance(before, datetime.datetime)
    assert isinstance(other_before, datetime.datetime)
    assert isinstance(how_long, datetime.timedelta)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    other_yesterday = today - relativedelta(days=1)
    how_long = today - yesterday
    assert isinstance(yesterday, datetime.date)
    assert isinstance(other_yesterday, datetime.date)
    assert isinstance(how_long, datetime.timedelta)


@freeze_time("2012-01-14")
def test_datetime_timezone_none():
    now = datetime.datetime.now(tz=None)
    now.should.equal(datetime.datetime(2012, 1, 14))


class GMT5(tzinfo):
    def utcoffset(self,dt):
        return timedelta(hours=5)
    def tzname(self,dt):
        return "GMT +5"
    def dst(self,dt):
        return timedelta(0)


@freeze_time("2012-01-14 2:00:00")
def test_datetime_timezone_real():
    now = datetime.datetime.now(tz=GMT5())
    now.should.equal(datetime.datetime(2012, 1, 14, 7, tzinfo=GMT5()))
    now.utcoffset().should.equal(timedelta(0, 60 * 60 * 5))


@freeze_time("2012-01-14 2:00:00", tz_offset=-4)
def test_datetime_timezone_real_with_offset():
    now = datetime.datetime.now(tz=GMT5())
    now.should.equal(datetime.datetime(2012, 1, 14, 3, tzinfo=GMT5()))
    now.utcoffset().should.equal(timedelta(0, 60 * 60 * 5))
