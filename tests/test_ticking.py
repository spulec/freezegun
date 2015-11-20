import datetime
import time
import mock

from freezegun import freeze_time
from tests import utils


@utils.cpython_only
def test_ticking_datetime():
    with freeze_time("Jan 14th, 2012", tick=True):
        time.sleep(0.001)  # Deal with potential clock resolution problems
        assert datetime.datetime.now() > datetime.datetime(2012, 1, 14)


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
