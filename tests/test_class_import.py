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
    fake_time,
    fake_localtime,
    fake_gmtime,
    fake_strftime,
)
import datetime


@freeze_time("2012-01-14")
def test_import_datetime_works() -> None:
    assert fake_datetime_function().day == 14


@freeze_time("2012-01-14")
def test_import_date_works() -> None:
    assert fake_date_function().day == 14


@freeze_time("2012-01-14")
def test_import_time() -> None:
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())
    assert fake_time_function() == expected_timestamp


def test_start_and_stop_works() -> None:
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


def test_isinstance_works() -> None:
    date = datetime.date.today()
    now = datetime.datetime.now()

    freezer = freeze_time('2011-01-01')
    freezer.start()
    assert isinstance(date, datetime.date)
    assert not isinstance(date, datetime.datetime)
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)
    freezer.stop()


def test_issubclass_works() -> None:
    real_date = datetime.date
    real_datetime = datetime.datetime

    freezer = freeze_time('2011-01-01')
    freezer.start()
    assert issubclass(real_date, datetime.date)
    assert issubclass(real_datetime, datetime.datetime)
    freezer.stop()


def test_fake_uses_real_when_ignored() -> None:
    real_time_before = time.time()
    with freeze_time('2012-01-14', ignore=['tests.fake_module']):
        real_time = fake_time_function()
    real_time_after = time.time()
    assert real_time_before <= real_time <= real_time_after


def test_can_ignore_email_module() -> None:
    from email.utils import formatdate
    with freeze_time('2012-01-14'):
        faked_date_str = formatdate()

    before_date_str = formatdate()
    with freeze_time('2012-01-14', ignore=['email']):
        date_str = formatdate()

    after_date_str = formatdate()
    assert date_str != faked_date_str
    assert before_date_str <= date_str <= after_date_str


@freeze_time('2011-01-01')
def test_avoid_replacing_equal_to_anything() -> None:
    assert fake_module.equal_to_anything.description == 'This is the equal_to_anything object'


@freeze_time("2012-01-14 12:00:00")
def test_import_localtime() -> None:
    struct = fake_localtime_function()
    assert struct.tm_year == 2012
    assert struct.tm_mon == 1
    assert struct.tm_mday >= 13  # eg. GMT+14
    assert struct.tm_mday <= 15  # eg. GMT-14


@freeze_time("2012-01-14 12:00:00")
def test_fake_gmtime_function() -> None:
    struct = fake_gmtime_function()
    assert struct.tm_year == 2012
    assert struct.tm_mon == 1
    assert struct.tm_mday == 14


@freeze_time("2012-01-14")
def test_fake_strftime_function() -> None:
    assert fake_strftime_function() == '2012'


def test_import_after_start() -> None:
    with freeze_time('2012-01-14'):
        assert 'tests.another_module' not in sys.modules.keys()
        from tests import another_module

        # Reals
        assert another_module.get_datetime() is datetime.datetime
        assert another_module.get_datetime() is FakeDatetime
        assert another_module.get_date() is datetime.date
        assert another_module.get_date() is FakeDate
        assert another_module.get_time() is time.time
        assert another_module.get_time() is fake_time
        assert another_module.get_localtime() is time.localtime
        assert another_module.get_localtime() is fake_localtime
        assert another_module.get_gmtime() is time.gmtime
        assert another_module.get_gmtime() is fake_gmtime
        assert another_module.get_strftime() is time.strftime
        assert another_module.get_strftime() is fake_strftime

        # Fakes
        assert another_module.get_fake_datetime() is FakeDatetime
        assert another_module.get_fake_date() is FakeDate
        assert another_module.get_fake_time() is fake_time
        assert another_module.get_fake_localtime() is fake_localtime
        assert another_module.get_fake_gmtime() is fake_gmtime
        assert another_module.get_fake_strftime() is fake_strftime

    # Reals
    assert another_module.get_datetime() is datetime.datetime
    assert not another_module.get_datetime() is FakeDatetime
    assert another_module.get_date() is datetime.date
    assert not another_module.get_date() is FakeDate
    assert another_module.get_time() is time.time
    assert not another_module.get_time() is fake_time
    assert another_module.get_localtime() is time.localtime
    assert not another_module.get_localtime() is fake_localtime
    assert another_module.get_gmtime() is time.gmtime
    assert not another_module.get_gmtime() is fake_gmtime
    assert another_module.get_strftime() is time.strftime
    assert not another_module.get_strftime() is fake_strftime

    # Fakes
    assert another_module.get_fake_datetime() is FakeDatetime
    assert another_module.get_fake_date() is FakeDate
    assert another_module.get_fake_time() is fake_time
    assert another_module.get_fake_localtime() is fake_localtime
    assert another_module.get_fake_gmtime() is fake_gmtime
    assert another_module.get_fake_strftime() is fake_strftime
    del sys.modules['tests.another_module']

def test_none_as_initial() -> None:
    with freeze_time() as ft:
        ft.move_to('2012-01-14')
        assert fake_strftime_function() == '2012'
