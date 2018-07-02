import datetime
import time
import mock

from freezegun import freeze_time
from nose.tools import assert_raises
from tests import utils

ONE_SECOND = datetime.timedelta(seconds=1)
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(days=1)

Y2K = datetime.datetime(year=2000, month=1, day=1)


@utils.cpython_only
def test_infinite_lazy_ticking_with_timedelta():
    with freeze_time("Jan 14th, 2012", lazy_tick=ONE_HOUR):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
        assert datetime.datetime.now() - datetime.datetime(2012, 1, 14) == ONE_HOUR


@utils.cpython_only
def test_infinite_lazy_ticking_with_true():
    with freeze_time("Jan 14th, 2012", lazy_tick=True):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
        assert datetime.datetime.now() - datetime.datetime(2012, 1, 14) == ONE_SECOND


def _next_datetimes_generator():
    for i in range(1, 4):
        yield Y2K + ONE_HOUR * i


def _test_finite_lazy_ticking(lazy_tick):
    with freeze_time(Y2K, lazy_tick=lazy_tick):
        for i in range(0, 4):
            datetime.datetime.now() == Y2K + ONE_HOUR * i

        assert_raises(StopIteration, datetime.datetime.now)


@utils.cpython_only
def test_finite_lazy_ticking_with_generator():
    _test_finite_lazy_ticking(_next_datetimes_generator())


@utils.cpython_only
def test_finite_lazy_ticking_with_iterable():
    next_datetimes_list = list(_next_datetimes_generator())
    _test_finite_lazy_ticking(next_datetimes_list)


@utils.cpython_only
def test_infinite_ticking_time_clock():
    with freeze_time('2012-01-14 03:21:34'):
        reference = time.clock()
        # Move forwards in time
        with freeze_time('2012-01-14 03:21:35', lazy_tick=ONE_HOUR):
            assert time.clock() - reference == 1
            assert time.clock() - reference == ONE_HOUR.total_seconds() + 1

        # Move backwards in time
        with freeze_time('2012-01-14 03:21:32', lazy_tick=-ONE_DAY):
            assert time.clock() - reference == - 2
            assert time.clock() - reference == - ONE_DAY.total_seconds() - 2


@utils.cpython_only
def test_ticking_date():
    with freeze_time("Jan 14th, 2012, 23:59:59.9999999", lazy_tick=True):
        assert datetime.date.today() == datetime.date(2012, 1, 14)
        assert datetime.date.today() == datetime.date(2012, 1, 15)


@utils.cpython_only
def test_ticking_time():
    with freeze_time("Jan 14th, 2012, 23:59:59", lazy_tick=True):
        assert time.time() == 1326585599.0
        assert time.time() == 1326585600.0


@mock.patch('freezegun.api._is_cpython', False)
def test_pypy_compat():
    try:
        freeze_time("Jan 14th, 2012, 23:59:59", lazy_tick=True)
    except SystemError:
        pass
    else:
        raise AssertionError("lazy_tick=True should error on non-CPython")


@mock.patch('freezegun.api._is_cpython', True)
def test_non_pypy_compat():
    try:
        freeze_time("Jan 14th, 2012, 23:59:59", lazy_tick=True)
    except Exception:
        raise AssertionError("lazy_tick=True should not error on CPython")
