import datetime
import functools
import sys

from dateutil import parser

real_date = datetime.date
real_datetime = datetime.datetime


class FakeDate(real_date):
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
        result = cls.date_to_freeze
        return date_to_fakedate(result)


class FakeDatetime(real_datetime, FakeDate):
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
        if tz:
            result = tz.fromutc(cls.time_to_freeze.replace(tzinfo=tz)) + datetime.timedelta(hours=cls.tz_offset)
        else:
            result = cls.time_to_freeze + datetime.timedelta(hours=cls.tz_offset)
        return datetime_to_fakedatetime(result)

    @classmethod
    def utcnow(cls):
        result = cls.time_to_freeze
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

        modules_for_datetime_faking = []
        modules_for_date_faking = []

        modules = sys.modules.values()

        for module in modules:
            if module is None:
                continue
            if module.__name__ != 'datetime':
                if hasattr(module, 'datetime') and module.datetime == real_datetime:
                    module.datetime = FakeDatetime
                if hasattr(module, 'date') and module.date == real_date:
                    module.date = FakeDate

        datetime.datetime.time_to_freeze = self.time_to_freeze
        datetime.datetime.tz_offset = self.tz_offset

        # Since datetime.datetime has already been mocket, just use that for
        # calculating the date
        datetime.date.date_to_freeze = datetime.datetime.now().date()

    def stop(self):
        datetime.datetime = real_datetime
        datetime.date = real_date

        for mod_name, module in sys.modules.items():
            if mod_name != 'datetime':
                if hasattr(module, 'datetime') and module.datetime == FakeDatetime:
                    module.datetime = real_datetime
                if hasattr(module, 'date') and module.date == FakeDate:
                    module.date = real_date

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)
