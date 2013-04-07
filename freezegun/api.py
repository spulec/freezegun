import ctypes
import datetime
import functools
import sys

from dateutil import parser
from forbiddenfruit import curse

real_date = datetime.date
real_datetime = datetime.datetime

real_datetime_now = real_datetime.now
real_datetime_utcnow = real_datetime.utcnow
real_date_today = real_date.today


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

        def fake_now(cls, tz=None):
            if tz:
                result = tz.fromutc(self.time_to_freeze.replace(tzinfo=tz)) + datetime.timedelta(hours=self.tz_offset)
            else:
                result = self.time_to_freeze + datetime.timedelta(hours=self.tz_offset)
            return result

        def fake_utcnow(cls):
            return self.time_to_freeze

        curse(real_datetime, "now", classmethod(fake_now))
        curse(real_datetime, "utcnow", classmethod(fake_utcnow))

        def fake_today(cls):
            now = fake_now(None)
            today = real_date(now.year, now.month, now.day)
            return today

        curse(real_date, "today", classmethod(fake_today))

    def stop(self):
        curse(real_datetime, "now", real_datetime_now)
        curse(real_datetime, "utcnow", real_datetime_utcnow)
        curse(real_date, "today", real_date_today)

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)
