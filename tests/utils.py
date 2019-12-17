from functools import wraps
from unittest import SkipTest
import datetime

from freezegun.api import FakeDate, FakeDatetime, _is_cpython


def is_fake_date(obj):
    return obj.__class__ is FakeDate


def is_fake_datetime(obj):
    return obj.__class__ is FakeDatetime


def cpython_only(func):
    @wraps(func)
    def wrapper(*args):
        if not _is_cpython:
            raise SkipTest("Requires CPython")
        return func(*args)
    return wrapper


if hasattr(datetime, 'timezone'):
    UTC = datetime.timezone.utc
else:
    class _Utc(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def dst(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return 0

    # Python 2.X doesn't have a built in UTC tzinfo, so we need to define one
    UTC = _Utc()
