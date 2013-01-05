import datetime
import functools

from dateutil import parser

real_date = datetime.date
real_datetime = datetime.datetime


class FakeDate(real_date):
    active = False
    date_to_freeze = None

    def __init__(self, *args, **kwargs):
        return real_date.__init__(*args, **kwargs)

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

    def __init__(self, *args, **kwargs):
        return real_datetime.__init__(*args, **kwargs)

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
    def now(cls):
        if cls.active:
            result = cls.time_to_freeze + datetime.timedelta(hours=cls.tz_offset)
        else:
            result = real_datetime.now()
        return datetime_to_fakedatetime(result)

    @classmethod
    def utcnow(cls):
        if cls.active:
            result = cls.time_to_freeze
        else:
            result = real_datetime.utcnow()
        return result

datetime.datetime = FakeDatetime
datetime.date = FakeDate


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
        datetime.datetime.time_to_freeze = self.time_to_freeze
        datetime.datetime.tz_offset = self.tz_offset
        datetime.datetime.active = True

        # Since datetime.datetime has already been mocket, just use that for
        # calculating the date
        datetime.date.date_to_freeze = datetime.datetime.now().date()
        datetime.date.active = True

    def stop(self):
        datetime.datetime.active = False
        datetime.date.active = False

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)
