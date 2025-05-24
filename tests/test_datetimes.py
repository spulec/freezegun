import time
import calendar
import datetime
import fractions
import unittest
import locale
import sys
from typing import Any, Callable
from unittest import SkipTest
from dateutil.tz import UTC

import pytest
from tests import utils

from freezegun import freeze_time
from freezegun.api import FakeDatetime, FakeDate

try:
    import maya  # type: ignore
except ImportError:
    maya = None

# time.clock was removed in Python 3.8
HAS_CLOCK = hasattr(time, 'clock')
HAS_TIME_NS = hasattr(time, 'time_ns')
HAS_MONOTONIC_NS = hasattr(time, 'monotonic_ns')
HAS_PERF_COUNTER_NS = hasattr(time, 'perf_counter_ns')

class temp_locale:
    """Temporarily change the locale."""

    def __init__(self, *targets: str):
        self.targets = targets

    def __enter__(self) -> None:
        self.old = locale.setlocale(locale.LC_ALL)
        for target in self.targets:
            try:
                locale.setlocale(locale.LC_ALL, target)
                return
            except locale.Error:
                pass
        msg = 'could not set locale to any of: %s' % ', '.join(self.targets)
        raise SkipTest(msg)

    def __exit__(self, *args: Any) -> None:
        locale.setlocale(locale.LC_ALL, self.old)

# Small sample of locales where '%x' expands to a dd/mm/yyyy string,
# which can cause trouble when parsed with dateutil.
_dd_mm_yyyy_locales = ['da_DK.UTF-8', 'de_DE.UTF-8', 'fr_FR.UTF-8']


def test_simple_api() -> None:
    # time to freeze is always provided in UTC
    freezer = freeze_time("2012-01-14")
    # expected timestamp must be a timestamp, corresponding to 2012-01-14 UTC
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())

    freezer.start()
    assert time.time() == expected_timestamp
    assert time.monotonic() >= 0.0
    assert time.perf_counter() >= 0.0
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14)
    assert datetime.date.today() == datetime.date(2012, 1, 14)
    assert datetime.datetime.now().today() == datetime.datetime(2012, 1, 14)
    freezer.stop()
    assert time.time() != expected_timestamp
    assert time.monotonic() >= 0.0
    assert time.perf_counter() >= 0.0
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() != datetime.datetime(2012, 1, 14)
    freezer = freeze_time("2012-01-10 13:52:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 10, 13, 52, 1)
    freezer.stop()


def test_tz_offset() -> None:
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


def test_timestamp_tz_offset() -> None:
    freezer = freeze_time(datetime.datetime.fromtimestamp(1), tz_offset=-1)
    freezer.start()
    t = datetime.datetime.now().timestamp()

    assert datetime.datetime.fromtimestamp(t).timestamp() == t
    freezer.stop()


def test_timedelta_tz_offset() -> None:
    freezer = freeze_time("2012-01-14 03:21:34",
                          tz_offset=-datetime.timedelta(hours=3, minutes=30))
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 51, 34)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14, 3, 21, 34)
    freezer.stop()


def test_tz_offset_with_today() -> None:
    freezer = freeze_time("2012-01-14", tz_offset=-4)
    freezer.start()
    assert datetime.date.today() == datetime.date(2012, 1, 13)
    freezer.stop()
    assert datetime.date.today() != datetime.date(2012, 1, 13)


def test_zero_tz_offset_with_time() -> None:
    # we expect the system to behave like a system with UTC timezone
    # at the beginning of the Epoch
    freezer = freeze_time('1970-01-01')
    freezer.start()
    assert datetime.date.today() == datetime.date(1970, 1, 1)
    assert datetime.datetime.now() == datetime.datetime(1970, 1, 1)
    assert datetime.datetime.utcnow() == datetime.datetime(1970, 1, 1)
    assert time.time() == 0.0
    assert time.monotonic() >= 0.0
    assert time.perf_counter() >= 0.0
    freezer.stop()


def test_tz_offset_with_time() -> None:
    # we expect the system to behave like a system with UTC-4 timezone
    # at the beginning of the Epoch (wall clock should be 4 hrs late)
    freezer = freeze_time('1970-01-01', tz_offset=-4)
    freezer.start()
    assert datetime.date.today() == datetime.date(1969, 12, 31)
    assert datetime.datetime.now() == datetime.datetime(1969, 12, 31, 20)
    assert datetime.datetime.utcnow() == datetime.datetime(1970, 1, 1)
    assert time.time() == 0.0
    assert time.monotonic() >= 0
    assert time.perf_counter() >= 0
    freezer.stop()


def test_time_with_microseconds() -> None:
    freezer = freeze_time(datetime.datetime(1970, 1, 1, 0, 0, 1, 123456))
    freezer.start()
    assert time.time() == 1.123456
    freezer.stop()


def test_time_with_dst() -> None:
    freezer = freeze_time(datetime.datetime(1970, 6, 1, 0, 0, 1, 123456))
    freezer.start()
    assert time.time() == 13046401.123456
    freezer.stop()


def test_manual_increment() -> None:
    initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                         hour=15, minute=6, second=3)
    with freeze_time(initial_datetime) as frozen_datetime:
        assert frozen_datetime() == initial_datetime

        expected = initial_datetime + datetime.timedelta(seconds=1)
        assert frozen_datetime.tick() == expected
        assert frozen_datetime() == expected

        expected = initial_datetime + datetime.timedelta(seconds=11)
        assert frozen_datetime.tick(10) == expected
        assert frozen_datetime() == expected

        expected = initial_datetime + datetime.timedelta(seconds=21)
        assert frozen_datetime.tick(delta=datetime.timedelta(seconds=10)) == expected
        assert frozen_datetime() == expected

        expected = initial_datetime + datetime.timedelta(seconds=22.5)
        ticked_time = frozen_datetime.tick(
            delta=fractions.Fraction(3, 2)  # type: ignore
            # type hints follow the recommendation of
            # https://peps.python.org/pep-0484/#the-numeric-tower
            # which means for instance `Fraction`s work at runtime, but not
            # during static type analysis
        )
        assert ticked_time == expected
        assert frozen_datetime() == expected


def test_move_to() -> None:
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


def test_bad_time_argument() -> None:
    try:
        freeze_time("2012-13-14", tz_offset=-4)
    except ValueError:
        pass
    else:
        assert False, "Bad values should raise a ValueError"


@pytest.mark.parametrize("func_name, has_func, tick_size", (
    ("monotonic", True, 1.0),
    ("monotonic_ns", HAS_MONOTONIC_NS, int(1e9)),
    ("perf_counter", True, 1.0),
    ("perf_counter_ns", HAS_PERF_COUNTER_NS, int(1e9)),)
)
def test_time_monotonic(func_name: str, has_func: bool, tick_size: int) -> None:
    initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                        hour=15, minute=6, second=3)
    if not has_func:
        pytest.skip("%s does not exist in current version" % func_name)

    with freeze_time(initial_datetime) as frozen_datetime:
        func = getattr(time, func_name)
        t0 = func()

        frozen_datetime.tick()

        t1 = func()

        assert t1 == t0 + tick_size

        frozen_datetime.tick(10)

        t11 = func()
        assert t11 == t1 + 10 * tick_size


def test_time_gmtime() -> None:
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


@pytest.mark.skipif(not HAS_CLOCK,
                    reason="time.clock was removed in Python 3.8")
def test_time_clock() -> None:
    with freeze_time('2012-01-14 03:21:34'):
        assert time.clock() == 0  # type: ignore[attr-defined]

        with freeze_time('2012-01-14 03:21:35'):
            assert time.clock() == 1  # type: ignore[attr-defined]

        with freeze_time('2012-01-14 03:21:36'):
            assert time.clock() == 2  # type: ignore[attr-defined]


class modify_timezone:

    def __init__(self, new_timezone: int):
        self.new_timezone = new_timezone
        self.original_timezone = time.timezone

    def __enter__(self) -> None:
        time.timezone = self.new_timezone

    def __exit__(self, *args: Any) -> None:
        time.timezone = self.original_timezone


def test_time_localtime() -> None:
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


def test_strftime() -> None:
    with modify_timezone(0):
        with freeze_time('1970-01-01'):
            assert time.strftime("%Y") == "1970"


def test_real_strftime_fall_through() -> None:
    this_real_year = datetime.datetime.now().year
    with freeze_time():
        assert time.strftime('%Y') == str(this_real_year)
        assert time.strftime('%Y', (2001, 1, 1, 1, 1, 1, 1, 1, 1)) == '2001'


def test_date_object() -> None:
    frozen_date = datetime.date(year=2012, month=11, day=10)
    date_freezer = freeze_time(frozen_date)
    regular_freezer = freeze_time('2012-11-10')
    assert date_freezer.time_to_freeze == regular_freezer.time_to_freeze


def test_old_date_object() -> None:
    frozen_date = datetime.date(year=1, month=1, day=1)
    with freeze_time(frozen_date):
        assert datetime.date.today() == frozen_date


def test_date_with_locale() -> None:
    with temp_locale(*_dd_mm_yyyy_locales):
        frozen_date = datetime.date(year=2012, month=1, day=2)
        date_freezer = freeze_time(frozen_date)
        assert date_freezer.time_to_freeze.date() == frozen_date


def test_invalid_type() -> None:
    try:
        freeze_time(int(4))  # type: ignore
    except TypeError:
        pass
    else:
        assert False, "Bad types should raise a TypeError"


def test_datetime_object() -> None:
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    datetime_freezer = freeze_time(frozen_datetime)
    regular_freezer = freeze_time('2012-11-10 04:15:30')
    assert datetime_freezer.time_to_freeze == regular_freezer.time_to_freeze


def test_function_object() -> None:
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    def function() -> datetime.datetime: return frozen_datetime

    with freeze_time(function):
        assert frozen_datetime == datetime.datetime.now()


def test_lambda_object() -> None:
    frozen_datetime = datetime.datetime(year=2012, month=11, day=10,
                                        hour=4, minute=15, second=30)
    with freeze_time(lambda: frozen_datetime):
        assert frozen_datetime == datetime.datetime.now()


def test_generator_object() -> None:
    frozen_datetimes = (datetime.datetime(year=y, month=1, day=1)
        for y in range(2010, 2012))

    with freeze_time(frozen_datetimes):
        assert datetime.datetime(2010, 1, 1) == datetime.datetime.now()

    with freeze_time(frozen_datetimes):
        assert datetime.datetime(2011, 1, 1) == datetime.datetime.now()

    with pytest.raises(StopIteration):
        freeze_time(frozen_datetimes)


def test_maya_datetimes() -> None:
    if not maya:
        raise SkipTest("maya is optional since it's not supported for "
                            "enough python versions")

    with freeze_time(maya.when("October 2nd, 1997")):
        assert datetime.datetime.now() == datetime.datetime(
            year=1997,
            month=10,
            day=2
        )


def test_old_datetime_object() -> None:
    frozen_datetime = datetime.datetime(year=1, month=7, day=12,
                                        hour=15, minute=6, second=3)
    with freeze_time(frozen_datetime):
        assert datetime.datetime.now() == frozen_datetime


def test_datetime_with_locale() -> None:
    with temp_locale(*_dd_mm_yyyy_locales):
        frozen_datetime = datetime.datetime(year=2012, month=1, day=2)
        date_freezer = freeze_time(frozen_datetime)
        assert date_freezer.time_to_freeze == frozen_datetime


@freeze_time("2012-01-14")
def test_decorator() -> None:
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


def test_decorator_wrapped_attribute() -> None:
    def to_decorate() -> None:
        pass

    wrapped = freeze_time("2014-01-14")(to_decorate)

    assert wrapped.__wrapped__ is to_decorate  # type: ignore


class Callable:  # type: ignore

    def __call__(self, *args: Any, **kws: Any) -> Any:
        return (args, kws)


@freeze_time("2012-01-14")
class Tester:

    def test_the_class(self) -> None:
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_still_the_same(self) -> None:
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_class_name_preserved_by_decorator(self) -> None:
        assert self.__class__.__name__ == "Tester"

    class NotATestClass:

        def perform_operation(self) -> datetime.date:
            return datetime.date.today()

    @freeze_time('2001-01-01')
    def test_class_decorator_ignores_nested_class(self) -> None:
        not_a_test = self.NotATestClass()
        assert not_a_test.perform_operation() == datetime.date(2001, 1, 1)

    a_mock = Callable()  # type: ignore

    def test_class_decorator_wraps_callable_object_py3(self) -> None:
        assert self.a_mock.__wrapped__.__class__ == Callable

    @staticmethod
    def helper() -> datetime.date:
        return datetime.date.today()

    def test_class_decorator_respects_staticmethod(self) -> None:
        assert self.helper() == datetime.date(2012, 1, 14)


@freeze_time("Jan 14th, 2012")
def test_nice_datetime() -> None:
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


@freeze_time("2012-01-14")
def test_datetime_date_method() -> None:
    now = datetime.datetime.now()
    assert now.date() == FakeDate(2012, 1, 14)


def test_context_manager() -> None:
    with freeze_time("2012-01-14"):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)


def test_nested_context_manager() -> None:
    with freeze_time("2012-01-14"):
        with freeze_time("2012-12-25"):
            _assert_datetime_date_and_time_are_all_equal(datetime.datetime(2012, 12, 25))
        _assert_datetime_date_and_time_are_all_equal(datetime.datetime(2012, 1, 14))
    assert datetime.datetime.now() > datetime.datetime(2013, 1, 1)


def _assert_datetime_date_and_time_are_all_equal(expected_datetime: datetime.datetime) -> None:
    assert datetime.datetime.now() == expected_datetime
    assert datetime.date.today() == expected_datetime.date()
    assert datetime.datetime.fromtimestamp(time.time()) == expected_datetime


def test_nested_context_manager_with_tz_offsets() -> None:
    with freeze_time("2012-01-14 23:00:00", tz_offset=2):
        with freeze_time("2012-12-25 19:00:00", tz_offset=6):
            assert datetime.datetime.now() == datetime.datetime(2012, 12, 26, 1)
            assert datetime.date.today() == datetime.date(2012, 12, 26)
            # no assertion for time.time() since it's not affected by tz_offset
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 15, 1)
        assert datetime.date.today() == datetime.date(2012, 1, 15)
    assert datetime.datetime.now() > datetime.datetime(2013, 1, 1)


@freeze_time("Jan 14th, 2012")
def test_isinstance_with_active() -> None:
    now = datetime.datetime.now()
    assert utils.is_fake_datetime(now)
    assert utils.is_fake_date(now.date())

    today = datetime.date.today()
    assert utils.is_fake_date(today)


def test_isinstance_without_active() -> None:
    now = datetime.datetime.now()
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)
    assert isinstance(now.date(), datetime.date)

    today = datetime.date.today()
    assert isinstance(today, datetime.date)


class TestUnitTestMethodDecorator(unittest.TestCase):
    @freeze_time('2013-04-09')
    def test_method_decorator_works_on_unittest(self) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    @freeze_time('2013-04-09', as_kwarg='frozen_time')
    def test_method_decorator_works_on_unittest_kwarg_frozen_time(self, frozen_time: Any) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())
        self.assertEqual(datetime.date(2013, 4, 9), frozen_time.time_to_freeze.date())

    @freeze_time('2013-04-09', as_kwarg='hello')
    def test_method_decorator_works_on_unittest_kwarg_hello(self, **kwargs: Any) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())
        self.assertEqual(datetime.date(2013, 4, 9), kwargs.get('hello').time_to_freeze.date())  # type: ignore

    @freeze_time(lambda: datetime.date(year=2013, month=4, day=9), as_kwarg='frozen_time')
    def test_method_decorator_works_on_unittest_kwarg_frozen_time_with_func(self, frozen_time: Any) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())
        self.assertEqual(datetime.date(2013, 4, 9), frozen_time.time_to_freeze.date())


@freeze_time('2013-04-09')
class TestUnitTestClassDecorator(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        assert datetime.date(2013, 4, 9) == datetime.date.today()

    def setUp(self) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    def tearDown(self) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    @classmethod
    def tearDownClass(cls) -> None:
        assert datetime.date(2013, 4, 9) == datetime.date.today()

    def test_class_decorator_works_on_unittest(self) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

    def test_class_name_preserved_by_decorator(self) -> None:
        self.assertEqual(self.__class__.__name__, "TestUnitTestClassDecorator")


@freeze_time('2013-04-09')
class TestUnitTestClassDecoratorWithNoSetUpOrTearDown(unittest.TestCase):
    def test_class_decorator_works_on_unittest(self) -> None:
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())


class TestUnitTestClassDecoratorSubclass(TestUnitTestClassDecorator):
    @classmethod
    def setUpClass(cls) -> None:
        # the super() call can fail if the class decoration was done wrong
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        # the super() call can fail if the class decoration was done wrong
        super().tearDownClass()

    def test_class_name_preserved_by_decorator(self) -> None:
        self.assertEqual(self.__class__.__name__,
                         "TestUnitTestClassDecoratorSubclass")


class BaseInheritanceFreezableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass


class UnfrozenInheritedTests(BaseInheritanceFreezableTests):
    def test_time_is_not_frozen(self) -> None:
        # In this class, time should not be frozen - and the below decorated
        # class shouldn't affect that
        self.assertNotEqual(datetime.date(2013, 4, 9), datetime.date.today())


@freeze_time('2013-04-09')
class FrozenInheritedTests(BaseInheritanceFreezableTests):
    def test_time_is_frozen(self) -> None:
        # In this class, time should be frozen
        self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())


class TestOldStyleClasses:
    def test_direct_method(self) -> None:
        # Make sure old style classes (not inheriting from object) is supported
        @freeze_time('2013-04-09')
        class OldStyleClass:
            def method(self) -> datetime.date:
                return datetime.date.today()

        assert OldStyleClass().method() == datetime.date(2013, 4, 9)

    def test_inherited_method(self) -> None:
        class OldStyleBaseClass:
            def inherited_method(self) -> datetime.date:
                return datetime.date.today()

        @freeze_time('2013-04-09')
        class OldStyleClass(OldStyleBaseClass):
            pass

        assert OldStyleClass().inherited_method() == datetime.date(2013, 4, 9)


def test_min_and_max() -> None:
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
def test_freeze_with_timezone_aware_datetime_in_utc() -> None:
    """
    utcnow() should always return a timezone naive datetime
    """
    utc_now = datetime.datetime.utcnow()
    assert utc_now.tzinfo is None


@freeze_time("1970-01-01T00:00:00-04:00")
def test_freeze_with_timezone_aware_datetime_in_non_utc() -> None:
    """
    we expect the system to behave like a system with UTC-4 timezone
    at the beginning of the Epoch (wall clock should be 4 hrs late)
    """
    utc_now = datetime.datetime.utcnow()
    assert utc_now.tzinfo is None
    assert utc_now == datetime.datetime(1970, 1, 1, 4)


@freeze_time('2015-01-01')
def test_time_with_nested() -> None:
    from time import time
    first = 1420070400.0
    second = 1420070760.0

    assert time() == first
    with freeze_time('2015-01-01T00:06:00'):
        assert time() == second


@pytest.mark.parametrize("func_name",
    ("monotonic", "perf_counter")
)
def test_monotonic_with_nested(func_name: str) -> None:
    __import__("time", fromlist=[func_name])
    invoke_time_func: Callable[[], float] = lambda: getattr(time, func_name)()

    with freeze_time('2015-01-01') as frozen_datetime_1:
        initial_t1 = invoke_time_func()
        with freeze_time('2015-12-25') as frozen_datetime_2:
            initial_t2 = invoke_time_func()
            frozen_datetime_2.tick()
            assert invoke_time_func() == initial_t2 + 1
        assert invoke_time_func() == initial_t1
        frozen_datetime_1.tick()
        assert invoke_time_func() == initial_t1 + 1


def test_should_use_real_time() -> None:
    frozen = datetime.datetime(2015, 3, 5)
    expected_frozen = 1425513600.0
    # TODO: local time seems to leak the local timezone, so this test fails in CI
    # expected_frozen_local = (2015, 3, 5, 1, 0, 0, 3, 64, -1)
    expected_frozen_gmt = (2015, 3, 5, 0, 0, 0, 3, 64, -1)
    expected_clock = 0

    from freezegun import api
    api.call_stack_inspection_limit = 100  # just to increase coverage

    timestamp_to_convert = 1579602312
    time_tuple = time.gmtime(timestamp_to_convert)

    with freeze_time(frozen):
        assert time.time() == expected_frozen
        # assert time.localtime() == expected_frozen_local
        assert time.gmtime() == expected_frozen_gmt
        if HAS_CLOCK:
            assert time.clock() == expected_clock  # type: ignore[attr-defined]
        if HAS_TIME_NS:
            assert time.time_ns() == expected_frozen * 1e9

        assert calendar.timegm(time.gmtime()) == expected_frozen
        assert calendar.timegm(time_tuple) == timestamp_to_convert

    with freeze_time(frozen, ignore=['_pytest']):
        assert time.time() != expected_frozen
        # assert time.localtime() != expected_frozen_local
        assert time.gmtime() != expected_frozen_gmt
        if HAS_CLOCK:
            assert time.clock() != expected_clock  # type: ignore[attr-defined]
        if HAS_TIME_NS:
            assert time.time_ns() != expected_frozen * 1e9

        assert calendar.timegm(time.gmtime()) != expected_frozen
        assert calendar.timegm(time_tuple) == timestamp_to_convert


@pytest.mark.skipif(not HAS_TIME_NS,
                    reason="time.time_ns is present only on 3.7 and above")
def test_time_ns() -> None:
    freezer = freeze_time("2012-01-14")
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())

    with freezer:
        assert time.time() == expected_timestamp
        assert time.time_ns() == expected_timestamp * 1e9

    assert time.time() != expected_timestamp
    assert time.time_ns() != expected_timestamp * 1e9


@pytest.mark.skipif(not HAS_TIME_NS,
                    reason="time.time_ns is present only on 3.7 and above")
def test_time_ns_with_microseconds() -> None:
    freezer = freeze_time("2024-03-20 18:21:10.12345")

    with freezer:
        assert time.time_ns() == 1710958870123450112

    assert time.time_ns() != 1710958870123450112


def test_compare_datetime_and_time_with_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Compare the result of datetime.datetime.now() and time.time() in a non-UTC timezone. These
    should be consistent.
    """
    try:
        with monkeypatch.context() as m, freeze_time("1970-01-01 00:00:00"):
            m.setenv("TZ", "Europe/Berlin")
            time.tzset()

            now = datetime.datetime.now()
            assert now == datetime.datetime.fromtimestamp(time.time())
            assert now == datetime.datetime.utcfromtimestamp(time.time())
            assert now == datetime.datetime.utcnow()
            assert now.timestamp() == time.time()
    finally:
        time.tzset()  # set the timezone back to what is was before


def test_timestamp_with_tzoffset() -> None:
    with freeze_time("2000-01-01", tz_offset=6):
        utcnow = datetime.datetime(2000, 1, 1, 0)
        nowtz = datetime.datetime(2000, 1, 1, 0, tzinfo=UTC)
        now = datetime.datetime(2000, 1, 1, 6)
        assert now == datetime.datetime.now()
        assert now == datetime.datetime.fromtimestamp(time.time())
        assert now.timestamp() == time.time()
        assert nowtz.timestamp() == time.time()

        assert utcnow == datetime.datetime.utcfromtimestamp(time.time())
        assert utcnow == datetime.datetime.utcnow()

@pytest.mark.skip("timezone handling is currently incorrect")
def test_datetime_in_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    It is assumed that the argument passed to freeze_time is in UTC, unless explicitly indicated
    otherwise. Therefore datetime.now() should return the frozen time with an offset.
    """
    try:
        with monkeypatch.context() as m, freeze_time("1970-01-01 00:00:00"):
            m.setenv("TZ", "Europe/Berlin")
            time.tzset()

            assert datetime.datetime.now() == datetime.datetime(1970, 1, 1, 1, 0, 0)
    finally:
        time.tzset()  # set the timezone back to what is was before
