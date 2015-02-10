import time
import datetime
import unittest
import locale

from nose.plugins import skip
from tests import utils

from freezegun import freeze_time
from freezegun.api import FakeDatetime, FakeDate


class temp_locale(object):
    """Temporarily change the locale."""

    def __init__(self, *targets):
        self.targets = targets

    def __enter__(self):
        self.old = locale.setlocale(locale.LC_ALL)
        for target in self.targets:
            try:
                locale.setlocale(locale.LC_ALL, target)
                return
            except locale.Error:
                pass
        msg = 'could not set locale to any of: %s' % ', '.join(self.targets)
        raise skip.SkipTest(msg)

    def __exit__(self, *args):
        locale.setlocale(locale.LC_ALL, self.old)

# Small sample of locales where '%x' expands to a dd/mm/yyyy string,
# which can cause trouble when parsed with dateutil.
_dd_mm_yyyy_locales = ['da_DK.UTF-8', 'de_DE.UTF-8', 'fr_FR.UTF-8']


def test_simple_api():
    # time to freeze is always provided in UTC
    freezer = freeze_time("2012-01-14")
    # expected timestamp must be a timestamp, corresponding to 2012-01-14 UTC
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())

    freezer.start()
    assert time.time() == expected_timestamp
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14)
    assert datetime.date.today() == datetime.date(2012, 1, 14)
    assert datetime.datetime.now().today() == datetime.datetime(2012, 1, 14)
    freezer.stop()
    assert time.time() != expected_timestamp
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() != datetime.datetime(2012, 1, 14)
    freezer = freeze_time("2012-01-10 13:52:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 10, 13, 52, 1)
    freezer.stop()


def test_tz_offset():
    freezer = freeze_time("2012-01-14 03:21:34", tz_offset=-4)
    # expected timestamp must be a timestamp,
    # corresponding to 2012-01-14 03:21:34 UTC
    # and it doesn't depend on tz_offset
    local_time = datetime.datetime(2012, 1, 14, 3, 21, 34)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())

    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 21, 34)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14, 3, 21, 34)
    assert time.time() == expected_timestamp
    freezer.stop()


def test_tz_offset_with_today():
    freezer = freeze_time("2012-01-14", tz_offset=-4)
    freezer.start()
    assert datetime.date.today() == datetime.date(2012, 1, 13)
    freezer.stop()
    assert datetime.date.today() != datetime.date(2012, 1, 13)


def test_zero_tz_offset_with_time():
    # we expect the system to behave like a system with UTC timezone
    # at the beginning of the Epoch
    freezer = freeze_time('1970-01-01')
    freezer.start()
    assert datetime.date.today() == datetime.date(1970, 1, 1)
    assert datetime.datetime.now() == datetime.datetime(1970, 1, 1)
    assert datetime.datetime.utcnow() == datetime.datetime(1970, 1, 1)
    assert time.time() == 0.0
    freezer.stop()


def test_tz_offset_with_time():
    # we expect the system to behave like a system with UTC-4 timezone
    # at the beginning of the Epoch (wall clock should be 4 hrs late)
    freezer = freeze_time('1970-01-01', tz_offset=-4)
    freezer.start()
    assert datetime.date.today() == datetime.date(1969, 12, 31)
    assert datetime.datetime.now() == datetime.datetime(1969, 12, 31, 20)
    assert datetime.datetime.utcnow() == datetime.datetime(1970, 1, 1)
    assert time.time() == 0.0
    freezer.stop()


def test_time_with_microseconds():
    freezer = freeze_time(datetime.datetime(1970, 1, 1, 0, 0, 1, 123456))
    freezer.start()
    assert time.time() == 1.123456
    freezer.stop()


def test_bad_time_argument():
    try:
        freeze_time("2012-13-14", tz_offset=-4)
    except ValueError:
        pass
    else:
        assert False, "Bad values should raise a ValueError"


def test_time_gmtime():
    with freeze_time('2012-01-14 03:21:34'):
        time_struct = time.gmtime()
        assert time_struct.tm_year == 2012
        assert time_struct.tm_mon == 1
        assert time_struct.tm_mday == 14
        assert time_struct.tm_hour == 3
        assert time_struct.tm_min == 21
        assert time_struct.tm_sec == 34
        assert time_struct.tm_wday == 5
        assert time_struct.tm_yday == 14
        assert time_struct.tm_isdst == -1


class modify_timezone(object):

    def __init__(self, new_timezone):
        self.new_timezone = new_timezone
        self.original_timezone = time.timezone

    def __enter__(self):
        time.timezone = self.new_timezone

    def __exit__(self, *args):
        time.timezone = self.original_timezone


def test_time_localtime():
    with modify_timezone(-3600):  # Set this for UTC-1
        with freeze_time('2012-01-14 03:21:34'):
            time_struct = time.localtime()
            assert time_struct.tm_year == 2012
            assert time_struct.tm_mon == 1
            assert time_struct.tm_mday == 14
            assert time_struct.tm_hour == 4  # offset of 1 hour due to time zone
            assert time_struct.tm_min == 21
            assert time_struct.tm_sec == 34
            assert time_struct.tm_wday == 5
            assert time_struct.tm_yday == 14
            assert time_struct.tm_isdst == -1


def test_strftime():
    with modify_timezone(0):
        with freeze_time('1970-01-01'):
            assert time.strftime("%Y") == "1970"


def test_date_object():
    frozen_date = datetime.date(year=2012, month=11, day=10)
    date_freezer = freeze_time(frozen_date)
    regular_freezer = freeze_time('2012-11-10')
    assert date_freezer.time_to_freeze == regular_freezer.time_to_freeze

def test_date_with_locale():
    with temp_locale(*_dd_mm_yyyy_locales):
        frozen_date = datetime.date(year=2012, month=1, day=2)
        date_freezer = freeze_time(frozen_date)
        assert date_freezer.time_to_freeze.date() == frozen_date

def test_invalid_type():
    try:
        freeze_time(int(4))
    except TypeError:
        pass
    else:
        assert False, "Bad types should raise a TypeError"


def test_datetime_object():
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    datetime_freezer = freeze_time(frozen_datetime)
    regular_freezer = freeze_time('2012-11-10 04:15:30')
    assert datetime_freezer.time_to_freeze == regular_freezer.time_to_freeze

def test_datetime_with_locale():
    with temp_locale(*_dd_mm_yyyy_locales):
        frozen_datetime = datetime.datetime(year=2012, month=1, day=2)
        date_freezer = freeze_time(frozen_datetime)
        assert date_freezer.time_to_freeze == frozen_datetime

@freeze_time("2012-01-14")
def test_decorator():
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


def test_decorator_wrapped_attribute():
    def to_decorate():
        pass

    wrapped = freeze_time("2014-01-14")(to_decorate)

    assert wrapped.__wrapped__ is to_decorate

@freeze_time("2012-01-14")
class Tester(object):
    def test_the_class(self):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_still_the_same(self):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


@freeze_time("Jan 14th, 2012")
def test_nice_datetime():
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


def test_context_manager():
    with freeze_time("2012-01-14"):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)


def test_nested_context_manager():
    with freeze_time("2012-01-14"):
        with freeze_time("2012-12-25"):
            _assert_datetime_date_and_time_are_all_equal(datetime.datetime(2012, 12, 25))
        _assert_datetime_date_and_time_are_all_equal(datetime.datetime(2012, 1, 14))
    assert datetime.datetime.now() > datetime.datetime(2013, 1, 1)


def _assert_datetime_date_and_time_are_all_equal(expected_datetime):
    assert datetime.datetime.now() == expected_datetime
    assert datetime.date.today() == expected_datetime.date()
    datetime_from_time = datetime.datetime.fromtimestamp(time.time())
    timezone_adjusted_datetime = datetime_from_time + datetime.timedelta(seconds=time.timezone)
    assert timezone_adjusted_datetime == expected_datetime


def test_nested_context_manager_with_tz_offsets():
    with freeze_time("2012-01-14 23:00:00", tz_offset=2):
        with freeze_time("2012-12-25 19:00:00", tz_offset=6):
            assert datetime.datetime.now() == datetime.datetime(2012, 12, 26, 1)
            assert datetime.date.today() == datetime.date(2012, 12, 26)
            #no assertion for time.time() since it's not affected by tz_offset
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 15, 1)
        assert datetime.date.today() == datetime.date(2012, 1, 15)
    assert datetime.datetime.now() > datetime.datetime(2013, 1, 1)


@freeze_time("Jan 14th, 2012")
def test_isinstance_with_active():
    now = datetime.datetime.now()
    assert utils.is_fake_datetime(now)

    today = datetime.date.today()
    assert utils.is_fake_date(today)


def test_isinstance_without_active():
    now = datetime.datetime.now()
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)

    today = datetime.date.today()
    assert isinstance(today, datetime.date)

@freeze_time('2013-04-09')
class TestUnitTestClassDecorator(unittest.TestCase):
    def setUp(self):
        self.assertEqual(datetime.date(2013,4,9), datetime.date.today())

    @classmethod
    def setUpClass(cls):
        assert datetime.date(2013,4,9) != datetime.date.today()

    def test_class_decorator_works_on_unittest(self):
        self.assertEqual(datetime.date(2013,4,9), datetime.date.today())

@freeze_time('2013-04-09')
class TestUnitTestClassDecoratorWithSetup(unittest.TestCase):
    def setUp(self):
        pass

    def test_class_decorator_works_on_unittest(self):
        self.assertEqual(datetime.date(2013,4,9), datetime.date.today())


def assert_class_of_datetimes(right_class, wrong_class):
    assert datetime.datetime.min.__class__ == right_class
    assert datetime.datetime.max.__class__ == right_class
    assert datetime.date.min.__class__ == right_class
    assert datetime.date.max.__class__ == right_class
    assert datetime.datetime.min.__class__ != wrong_class
    assert datetime.datetime.max.__class__ != wrong_class
    assert datetime.date.min.__class__ != wrong_class
    assert datetime.date.max.__class__ != wrong_class


def test_min_and_max():
    freezer = freeze_time("2012-01-14")
    real_datetime = datetime.datetime
    real_date = datetime.date

    freezer.start()
    assert datetime.datetime.min.__class__ == FakeDatetime
    assert datetime.datetime.max.__class__ == FakeDatetime
    assert datetime.date.min.__class__ == FakeDate
    assert datetime.date.max.__class__ == FakeDate
    assert datetime.datetime.min.__class__ != real_datetime
    assert datetime.datetime.max.__class__ != real_datetime
    assert datetime.date.min.__class__ != real_date
    assert datetime.date.max.__class__ != real_date

    freezer.stop()
    assert datetime.datetime.min.__class__ == datetime.datetime
    assert datetime.datetime.max.__class__ == datetime.datetime
    assert datetime.date.min.__class__ == datetime.date
    assert datetime.date.max.__class__ == datetime.date
    assert datetime.datetime.min.__class__ != FakeDatetime
    assert datetime.datetime.max.__class__ != FakeDatetime
    assert datetime.date.min.__class__ != FakeDate
    assert datetime.date.max.__class__ != FakeDate


@freeze_time("2014-07-30T01:00:00Z")
def test_freeze_with_timezone_aware_datetime_in_utc():
    """
    utcnow() should always return a timezone naive datetime
    """
    utc_now = datetime.datetime.utcnow()
    assert utc_now.tzinfo == None


@freeze_time("1970-01-01T00:00:00-04:00")
def test_freeze_with_timezone_aware_datetime_in_non_utc():
    """
    we expect the system to behave like a system with UTC-4 timezone
    at the beginning of the Epoch (wall clock should be 4 hrs late)
    """
    utc_now = datetime.datetime.utcnow()
    assert utc_now.tzinfo == None
    assert utc_now == datetime.datetime(1970, 1, 1, 4)
