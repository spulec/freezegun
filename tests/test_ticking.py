import datetime
import sys
import time

from unittest import mock
import pytest

from freezegun import freeze_time
from tests import utils

@utils.cpython_only
def test_ticking_datetime():
    with freeze_time("Jan 14th, 2012", tick=True):
        time.sleep(0.001)  # Deal with potential clock resolution problems
        assert datetime.datetime.now() > datetime.datetime(2012, 1, 14)


@pytest.mark.skipif(not hasattr(time, "clock"),
                    reason="time.clock was removed in Python 3.8")
@utils.cpython_only
def test_ticking_time_clock():
    with freeze_time('2012-01-14 03:21:34', tick=True):
        first = time.clock()
        time.sleep(0.001)  # Deal with potential clock resolution problems
        with freeze_time('2012-01-14 03:21:35', tick=True):
            second = time.clock()
            time.sleep(0.001)  # Deal with potential clock resolution problems

        with freeze_time('2012-01-14 03:21:36', tick=True):
            third = time.clock()
            time.sleep(0.001)

        # Rewind time backwards
        with freeze_time('2012-01-14 03:20:00', tick=True):
            fourth = time.clock()
            time.sleep(0.001)
            fifth = time.clock()

        assert first > 0
        assert second > first
        assert second > 1
        assert third > second
        assert third > 2

        assert third > fourth
        assert second > fourth
        assert first > fourth

        assert fifth > fourth


@utils.cpython_only
def test_ticking_date():
    with freeze_time("Jan 14th, 2012, 23:59:59.9999999", tick=True):
        time.sleep(0.001)  # Deal with potential clock resolution problems
        assert datetime.date.today() == datetime.date(2012, 1, 15)


@utils.cpython_only
def test_ticking_time():
    with freeze_time("Jan 14th, 2012, 23:59:59", tick=True):
        time.sleep(0.001)  # Deal with potential clock resolution problems
        assert time.time() > 1326585599.0


@utils.cpython_only_mark
@pytest.mark.parametrize("func_name",
    ("monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns"),
)
def test_ticking_monotonic(func_name):
    if sys.version_info[0:2] >= (3, 7):
        # All of these functions should exist in Python 3.7+, so this test helps
        # avoid inappropriate skipping when we've accidentally typo-ed the name
        # of one of these functions 😅
        assert hasattr(time, func_name)
    else:
        if not hasattr(time, func_name):
            pytest.skip(
                "time.%s does not exist in the current Python version" % func_name)

    func = getattr(time, func_name)
    with freeze_time("Jan 14th, 2012, 23:59:59", tick=True):
        initial = func()
        time.sleep(0.001)  # Deal with potential clock resolution problems
        assert func() > initial


@mock.patch('freezegun.api._is_cpython', False)
def test_pypy_compat():
    try:
        freeze_time("Jan 14th, 2012, 23:59:59", tick=True)
    except SystemError:
        pass
    else:
        raise AssertionError("tick=True should error on non-CPython")


@mock.patch('freezegun.api._is_cpython', True)
def test_non_pypy_compat():
    try:
        freeze_time("Jan 14th, 2012, 23:59:59", tick=True)
    except Exception:
        raise AssertionError("tick=True should not error on CPython")
