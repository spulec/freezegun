import time
import sys
from .fake_module import (
    fake_date_function,
    fake_datetime_function,
    fake_gmtime_function,
    fake_localtime_function,
    fake_strftime_function,
    fake_time_function,
)
from . import fake_module
from freezegun import freeze_time
from freezegun.api import (
    FakeDatetime,
    FakeDate,
    FakeTime,
    FakeLocalTime,
    FakeGMTTime,
    FakeStrfTime,
)
import datetime


@freeze_time("2012-01-14")
def test_import_datetime_works():
    assert fake_datetime_function().day == 14


@freeze_time("2012-01-14")
def test_import_date_works():
    assert fake_date_function().day == 14


@freeze_time("2012-01-14")
def test_import_time():
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())
    assert fake_time_function() == expected_timestamp


def test_start_and_stop_works():
    freezer = freeze_time("2012-01-14")

    result = fake_datetime_function()
    assert result.__class__ == datetime.datetime
    assert result.__class__ != FakeDatetime

    freezer.start()
    assert fake_datetime_function().day == 14
    assert isinstance(fake_datetime_function(), datetime.datetime)
    assert isinstance(fake_datetime_function(), FakeDatetime)

    freezer.stop()
    result = fake_datetime_function()
    assert result.__class__ == datetime.datetime
    assert result.__class__ != FakeDatetime


def test_isinstance_works():
    date = datetime.date.today()
    now = datetime.datetime.now()

    freezer = freeze_time('2011-01-01')
    freezer.start()
    assert isinstance(date, datetime.date)
    assert not isinstance(date, datetime.datetime)
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)
    freezer.stop()


@freeze_time('2011-01-01')
def test_avoid_replacing_equal_to_anything():
    assert fake_module.equal_to_anything.description == 'This is the equal_to_anything object'


@freeze_time("2012-01-14 12:00:00")
def test_import_localtime():
    struct = fake_localtime_function()
    assert struct.tm_year == 2012
    assert struct.tm_mon == 1
    assert struct.tm_mday >= 13  # eg. GMT+14
    assert struct.tm_mday <= 15  # eg. GMT-14


@freeze_time("2012-01-14 12:00:00")
def test_fake_gmtime_function():
    struct = fake_gmtime_function()
    assert struct.tm_year == 2012
    assert struct.tm_mon == 1
    assert struct.tm_mday == 14


@freeze_time("2012-01-14")
def test_fake_strftime_function():
    assert fake_strftime_function() == '2012'


def test_import_after_start():
    with freeze_time('2012-01-14'):
        assert 'tests.another_module' not in sys.modules.keys()
        from tests import another_module

        # Reals
        assert another_module.get_datetime() is datetime.datetime
        assert another_module.get_datetime() is FakeDatetime
        assert another_module.get_date() is datetime.date
        assert another_module.get_date() is FakeDate
        assert another_module.get_time() is time.time
        assert isinstance(another_module.get_time(), FakeTime)
        assert another_module.get_localtime() is time.localtime
        assert isinstance(another_module.get_localtime(), FakeLocalTime)
        assert another_module.get_gmtime() is time.gmtime
        assert isinstance(another_module.get_gmtime(), FakeGMTTime)
        assert another_module.get_strftime() is time.strftime
        assert isinstance(another_module.get_strftime(), FakeStrfTime)

        # Fakes
        assert another_module.get_fake_datetime() is FakeDatetime
        assert another_module.get_fake_date() is FakeDate
        assert another_module.get_fake_time() is FakeTime
        assert another_module.get_fake_localtime() is FakeLocalTime
        assert another_module.get_fake_gmtime() is FakeGMTTime
        assert another_module.get_fake_strftime() is FakeStrfTime

    # Reals
    assert another_module.get_datetime() is datetime.datetime
    assert not another_module.get_datetime() is FakeDatetime
    assert another_module.get_date() is datetime.date
    assert not another_module.get_date() is FakeDate
    assert another_module.get_time() is time.time
    assert not isinstance(another_module.get_time(), FakeTime)
    assert another_module.get_localtime() is time.localtime
    assert not isinstance(another_module.get_localtime(), FakeLocalTime)
    assert another_module.get_gmtime() is time.gmtime
    assert not isinstance(another_module.get_gmtime(), FakeGMTTime)
    assert another_module.get_strftime() is time.strftime
    assert not isinstance(another_module.get_strftime(), FakeStrfTime)

    # Fakes
    assert another_module.get_fake_datetime() is FakeDatetime
    assert another_module.get_fake_date() is FakeDate
    assert another_module.get_fake_time() is FakeTime
    assert another_module.get_fake_localtime() is FakeLocalTime
    assert another_module.get_fake_gmtime() is FakeGMTTime
    assert another_module.get_fake_strftime() is FakeStrfTime


def test_none_as_initial():
    with freeze_time() as ft:
        ft.move_to('2012-01-14')
        assert fake_strftime_function() == '2012'
