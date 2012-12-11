import datetime
import functools

real_date = datetime.date
real_datetime = datetime.datetime

class FakeDate(real_date):
    time_to_freeze = None
    def __new__(cls, *args, **kwargs):
        return real_date.__new__(real_date, *args, **kwargs)

    @classmethod
    def today(cls):
        return cls.time_to_freeze

class FakeDatetime(real_datetime):
    time_to_freeze = None
    def __new__(cls, *args, **kwargs):
        return real_datetime.__new__(real_datetime, *args, **kwargs)

    @classmethod
    def now(cls):
        return cls.time_to_freeze

    @classmethod
    def utcnow(cls):
        # TODO: fix
        return cls.time_to_freeze


class _freeze_time():

    def __init__(self, time_to_freeze):
        self.time_to_freeze = time_to_freeze

    def __call__(self, func):
        return self.decorate_callable(func)

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        datetime.date = FakeDate
        datetime.datetime = FakeDatetime

        time_to_freeze = datetime.datetime.strptime(self.time_to_freeze, "%Y-%m-%d")
        datetime.date.time_to_freeze = time_to_freeze.date()
        datetime.datetime.time_to_freeze = time_to_freeze

    def stop(self):
        datetime.date = real_date
        datetime.datetime = real_datetime

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper

def freeze_time(time_to_freeze):
    return _freeze_time(time_to_freeze)
