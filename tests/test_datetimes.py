import time
import datetime
import unittest
import locale
import sys

from nose.plugins import skip
from nose.tools import assert_raises
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


def test_timedelta_tz_offset():
    freezer = freeze_time("2012-01-14 03:21:34",
                          tz_offset=-datetime.timedelta(hours=3, minutes=30))
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 51, 34)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14, 3, 21, 34)
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


def test_time_with_dst():
    freezer = freeze_time(datetime.datetime(1970, 6, 1, 0, 0, 1, 123456))
    freezer.start()
    assert time.time() == 13046401.123456
    freezer.stop()


def test_manual_increment():
    initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                        hour=15, minute=6, second=3)
    with freeze_time(initial_datetime) as frozen_datetime:
        assert frozen_datetime() == initial_datetime

        frozen_datetime.tick()
        initial_datetime += datetime.timedelta(seconds=1)
        assert frozen_datetime() == initial_datetime

        frozen_datetime.tick(delta=datetime.timedelta(seconds=10))
        initial_datetime += datetime.timedelta(seconds=10)
        assert frozen_datetime() == initial_datetime


def test_manual_increment_seconds():
    initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                         hour=15, minute=6, second=3)
    with freeze_time(initial_datetime) as frozen_datetime:
        assert frozen_datetime() == initial_datetime

        frozen_datetime.tick()
        initial_datetime += datetime.timedelta(seconds=1)
        assert frozen_datetime() == initial_datetime

        frozen_datetime.tick(10)
        initial_datetime += datetime.timedelta(seconds=10)
        assert frozen_datetime() == initial_datetime


def test_move_to():
    initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                        hour=15, minute=6, second=3)

    other_datetime = datetime.datetime(year=2, month=8, day=13,
                                        hour=14, minute=5, second=0)
    with freeze_time(initial_datetime) as frozen_datetime:
        assert frozen_datetime() == initial_datetime

        frozen_datetime.move_to(other_datetime)
        assert frozen_datetime() == other_datetime

        frozen_datetime.move_to(initial_datetime)
        assert frozen_datetime() == initial_datetime


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
    assert time.localtime().tm_year != 2012


def test_strftime():
    with modify_timezone(0):
        with freeze_time('1970-01-01'):
            assert time.strftime("%Y") == "1970"


def test_date_object():
    frozen_date = datetime.date(year=2012, month=11, day=10)
    date_freezer = freeze_time(frozen_date)
    regular_freezer = freeze_time('2012-11-10')
    assert date_freezer.time_to_freeze == regular_freezer.time_to_freeze


def test_old_date_object():
    frozen_date = datetime.date(year=1, month=1, day=1)
    with freeze_time(frozen_date):
        assert datetime.date.today() == frozen_date


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


def test_function_object():
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    def function(): return frozen_datetime

    with freeze_time(function):
        assert frozen_datetime == datetime.datetime.now()


def test_lambda_object():
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    with freeze_time(lambda: frozen_datetime):
        assert frozen_datetime == datetime.datetime.now()


def test_generator_object():
    frozen_datetimes = (datetime.datetime(year=y, month=1, day=1)
        for y in range(2010, 2012))

    with freeze_time(frozen_datetimes):
        assert datetime.datetime(2010, 1, 1) == datetime.datetime.now()

    with freeze_time(frozen_datetimes):
        assert datetime.datetime(2011, 1, 1) == datetime.datetime.now()

    assert_raises(StopIteration, freeze_time, frozen_datetimes)


def test_old_datetime_object():
    frozen_datetime = datetime.datetime(year=1, month=7, day=12,
                                        hour=15, minute=6, second=3)
    with freeze_time(frozen_datetime):
        assert datetime.datetime.now() == frozen_datetime


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


class Callable(object):

    def __call__(self, *args, **kws):
        return (args, kws)


@freeze_time("2012-01-14")
class Tester(object):

    def test_the_class(self):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_still_the_same(self):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_class_name_preserved_by_decorator(self):
        assert self.__class__.__name__ == "Tester"

    class NotATestClass(object):

        def perform_operation(self):
            return datetime.date.today()

    @freeze_time('2001-01-01')
    def test_class_decorator_ignores_nested_class(self):
        not_a_test = self.NotATestClass()
        assert not_a_test.perform_operation() == datetime.date(2001, 1, 1)

    a_mock = Callable()

    def test_class_decorator_skips_callable_object_py2(self):
        if sys.version_info[0] != 2:
            raise skip.SkipTest("test target is Python2")
        assert self.a_mock.__class__ == Callable

    def test_class_decorator_wraps_callable_object_py3(self):
        if sys.version_info[0] != 3:
            raise skip.SkipTest("test target is Python3")
        assert self.a_mock.__wrapped__.__class__ == Callable

    @staticmethod
    def helper():
        return datetime.date.today()

    def test_class_decorator_respects_staticmethod(self):
        assert self.helper() == datetime.date(2012, 1, 14)


@freeze_time("Jan 14th, 2012")
def test_nice_datetime():
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


@freeze_time("2012-01-14")
def test_datetime_date_method():
    now = datetime.datetime.now()
    assert now.date() == FakeDate(2012, 1, 14)


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
            # no assertion for time.time() since it's not affected by tz_offset
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 15, 1)
        assert datetime.date.today() == datetime.date(2012, 1, 15)
    assert datetime.datetime.now() > datetime.datetime(2013, 1, 1)


@freeze_time("Jan 14th, 2012")
def test_isinstance_with_active():
    now = datetime.datetime.now()
    assert utils.is_fake_datetime(now)
    assert utils.is_fake_date(now.date())

    today = datetime.date.today()
    assert utils.is_fake_date(today)


def test_isinstance_without_active():
    now = datetime.datetime.now()
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)
    assert isinstance(now.date(), datetime.date)

    today = datetime.date.today()
    assert isinstance(today, datetime.date)


@freeze_time('2013-04-09')
class TestUnitTestClassDecorator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert datetime.date(2013, 4, 9) == datetime.date.today()

    def setUp(self):
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    def tearDown(self):
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    @classmethod
    def tearDownClass(cls):
        assert datetime.date(2013, 4, 9) == datetime.date.today()

    def test_class_decorator_works_on_unittest(self):
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    def test_class_name_preserved_by_decorator(self):
        self.assertEqual(self.__class__.__name__, "TestUnitTestClassDecorator")


@freeze_time('2013-04-09')
class TestUnitTestClassDecoratorWithNoSetUpOrTearDown(unittest.TestCase):
    def test_class_decorator_works_on_unittest(self):
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())


class TestUnitTestClassDecoratorSubclass(TestUnitTestClassDecorator):
    @classmethod
    def setUpClass(cls):
        # the super() call can fail if the class decoration was done wrong
        super(TestUnitTestClassDecoratorSubclass, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # the super() call can fail if the class decoration was done wrong
        super(TestUnitTestClassDecoratorSubclass, cls).tearDownClass()

    def test_class_name_preserved_by_decorator(self):
        self.assertEqual(self.__class__.__name__,
                         "TestUnitTestClassDecoratorSubclass")


class BaseInheritanceFreezableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


class UnfrozenInheritedTests(BaseInheritanceFreezableTests):
    def test_time_is_not_frozen(self):
        # In this class, time should not be frozen - and the below decorated
        # class shouldn't affect that
        self.assertNotEqual(datetime.date(2013, 4, 9), datetime.date.today())


@freeze_time('2013-04-09')
class FrozenInheritedTests(BaseInheritanceFreezableTests):
    def test_time_is_frozen(self):
        # In this class, time should be frozen
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())


class TestOldStyleClasses:
    def test_direct_method(self):
        # Make sure old style classes (not inheriting from object) is supported
        @freeze_time('2013-04-09')
        class OldStyleClass:
            def method(self):
                return datetime.date.today()

        assert OldStyleClass().method() == datetime.date(2013, 4, 9)

    def test_inherited_method(self):
        class OldStyleBaseClass:
            def inherited_method(self):
                return datetime.date.today()

        @freeze_time('2013-04-09')
        class OldStyleClass(OldStyleBaseClass):
            pass

        assert OldStyleClass().inherited_method() == datetime.date(2013, 4, 9)


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
    assert utc_now.tzinfo is None


@freeze_time("1970-01-01T00:00:00-04:00")
def test_freeze_with_timezone_aware_datetime_in_non_utc():
    """
    we expect the system to behave like a system with UTC-4 timezone
    at the beginning of the Epoch (wall clock should be 4 hrs late)
    """
    utc_now = datetime.datetime.utcnow()
    assert utc_now.tzinfo is None
    assert utc_now == datetime.datetime(1970, 1, 1, 4)
