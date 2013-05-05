import datetime
import unittest

from freezegun import freeze_time


def test_simple_api():
    freezer = freeze_time("2012-01-14")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14)
    assert datetime.date.today() == datetime.date(2012, 1, 14)
    assert datetime.datetime.now().today() == datetime.date(2012, 1, 14)
    freezer.stop()
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
    assert datetime.datetime.utcnow() != datetime.datetime(2012, 1, 14)
    freezer = freeze_time("2012-01-10 13:52:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 10, 13, 52, 1)
    freezer.stop()


def test_tz_offset():
    freezer = freeze_time("2012-01-14 03:21:34", tz_offset=-4)
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 21, 34)
    assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14, 3, 21, 34)
    freezer.stop()


def test_tz_offset_with_today():
    freezer = freeze_time("2012-01-14", tz_offset=-4)
    freezer.start()
    assert datetime.date.today() == datetime.date(2012, 1, 13)
    freezer.stop()
    assert datetime.date.today() != datetime.date(2012, 1, 13)


def test_bad_time_argument():
    try:
        freeze_time("2012-13-14", tz_offset=-4)
    except ValueError:
        pass
    else:
        assert False, "Bad values should raise a ValueError"


def test_date_object():
    frozen_date = datetime.date(year=2012, month=11, day=10)
    date_freezer = freeze_time(frozen_date)
    regular_freezer = freeze_time('2012-11-10')
    assert date_freezer.time_to_freeze == regular_freezer.time_to_freeze


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


@freeze_time("2012-01-14")
def test_decorator():
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)


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


@freeze_time("Jan 14th, 2012")
def test_isinstance_with_active():
    now = datetime.datetime.now()
    assert isinstance(now, datetime.datetime)

    today = datetime.date.today()
    assert isinstance(today, datetime.date)


def test_isinstance_without_active():
    now = datetime.datetime.now()
    assert isinstance(now, datetime.datetime)
    assert isinstance(now, datetime.date)

    today = datetime.date.today()
    assert isinstance(today, datetime.date)

@freeze_time('2013-04-09')
class TestUnitTestClassDecorator(unittest.TestCase):
    def test_class_decorator_works_on_unittest(self):
        self.assertEqual(datetime.date(2013,4,9), datetime.date.today())
