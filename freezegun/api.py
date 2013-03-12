#pylint:disable=C0103,W0621,C0111,W0201
"""
FreezeGun allows you to freeze a moment in time as far as the Python Interpreter is concerned

"""


import datetime
import time
import functools

from dateutil import parser

real_date = datetime.date
real_datetime = datetime.datetime


class FakeTime(object):
    """
    a mock of time
    """
    def __init__(self):
        self.old_time_func = time.time
        self.frozen_time = None

    def start_mock(self, freeze_time=None):
        """
        install the mock
        """
        if freeze_time is None:
            self.frozen_time = time.time()
        else:
            self.frozen_time = time.mktime(freeze_time.timetuple())
        self.old_time_func = time.time
        time.time = self.unix_time_mock

    def stop_mock(self):
        """
        replace the old time func
        """
        time.time = self.old_time_func

    def unix_time_mock(self):
        """
        an example of time unix_time_mock
        """
        return self.frozen_time


class FakeDate(real_date):
    active = False
    date_to_freeze = None

    def __new__(cls, *args, **kwargs):
        return real_date.__new__(cls, *args, **kwargs)

    def __add__(self, other):
        result = super(FakeDate, self).__add__(other)
        if result is NotImplemented:
            return result
        return date_to_fakedate(result)

    def __sub__(self, other):
        result = super(FakeDate, self).__sub__(other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_date):
            return date_to_fakedate(result)
        else:
            return result

    @classmethod
    def today(cls):
        if cls.active:
            result = cls.date_to_freeze
        else:
            result = real_date.today()
        return date_to_fakedate(result)


class FakeDatetime(real_datetime, FakeDate):
    active = False
    time_to_freeze = None
    tz_offset = None

    def __new__(cls, *args, **kwargs):
        return real_datetime.__new__(cls, *args, **kwargs)

    def __add__(self, other):
        result = super(FakeDatetime, self).__add__(other)
        if result is NotImplemented:
            return result
        return datetime_to_fakedatetime(result)

    def __sub__(self, other):
        result = super(FakeDatetime, self).__sub__(other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_datetime):
            return datetime_to_fakedatetime(result)
        else:
            return result

    @classmethod
    def now(cls, tz=None):
        if cls.active:
            result = cls.time_to_freeze + datetime.timedelta(hours=cls.tz_offset)
        else:
            result = real_datetime.now(tz)
        return datetime_to_fakedatetime(result)

    @classmethod
    def utcnow(cls):
        if cls.active:
            result = cls.time_to_freeze
        else:
            result = real_datetime.utcnow()
        return result

def datetime_to_fakedatetime(datetime):
    return FakeDatetime(datetime.year,
                        datetime.month,
                        datetime.day,
                        datetime.hour,
                        datetime.minute,
                        datetime.second,
                        datetime.microsecond,
                        datetime.tzinfo)


def date_to_fakedate(date):
    return FakeDate(date.year,
                    date.month,
                    date.day)

def datetime_to_faketime(datetime):
    return FakeTime(time.mktime(datetime.timetuple()))


class _freeze_time():

    def __init__(self, time_to_freeze_str, tz_offset):
        time_to_freeze = parser.parse(time_to_freeze_str)

        self.time_to_freeze = time_to_freeze
        self.tz_offset = tz_offset

    def __call__(self, func):
        return self.decorate_callable(func)

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        datetime.datetime = FakeDatetime
        datetime.date = FakeDate

        datetime.datetime.time_to_freeze = self.time_to_freeze
        datetime.datetime.tz_offset = self.tz_offset
        datetime.datetime.active = True

        # Since datetime.datetime has already been mocket, just use that for
        # calculating the date
        datetime.date.date_to_freeze = datetime.datetime.now().date()
        datetime.date.active = True

        self.fake_time = FakeTime()
        self.fake_time.start_mock(datetime.datetime.time_to_freeze)

    def stop(self):
        datetime.datetime.active = False
        datetime.date.active = False

        datetime.datetime = real_datetime
        datetime.date = real_date

        self.fake_time.stop_mock()

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)