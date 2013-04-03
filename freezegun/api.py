import ctypes
import datetime
import functools
import sys

from dateutil import parser
from .magic import patchable_builtin as ctype_dict

real_date = datetime.date
real_datetime = datetime.datetime

real_datetime_now = real_datetime.now
real_datetime_utcnow = real_datetime.utcnow
real_date_today = real_date.today


class FakeDate(object):

    def __init__(self, date_to_freeze):
        self.date_to_freeze = date_to_freeze

    def today(self):
        return self.date_to_freeze


class FakeDatetime(object):


    def __init__(self, time_to_freeze, tz_offset):
        self.time_to_freeze = time_to_freeze
        self.tz_offset = tz_offset

    def now(self, tz=None):
        if tz:
            result = tz.fromutc(self.time_to_freeze.replace(tzinfo=tz)) + datetime.timedelta(hours=self.tz_offset)
        else:
            result = self.time_to_freeze + datetime.timedelta(hours=self.tz_offset)
        return result

    def utcnow(self):
        return self.time_to_freeze


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
        fake_datetime = FakeDatetime(self.time_to_freeze, self.tz_offset)
        datetime_dict = ctype_dict(real_datetime)
        datetime_dict['now'] = fake_datetime.now
        datetime_dict['utcnow'] = fake_datetime.utcnow

        now = datetime.datetime.now()
        today = real_date(now.year, now.month, now.day)
        fake_date = FakeDate(today)
        date_dict = ctype_dict(real_date)
        date_dict['today'] = fake_date.today

    def stop(self):
        datetime_dict = ctype_dict(real_datetime)
        datetime_dict['now'] = real_datetime_now
        datetime_dict['utcnow'] = real_datetime_utcnow

        date_dict = ctype_dict(real_date)
        date_dict['today'] = real_date_today

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)
