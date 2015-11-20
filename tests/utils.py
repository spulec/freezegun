from functools import wraps

from nose.plugins import skip

from freezegun.api import FakeDate, FakeDatetime, _is_cpython


def is_fake_date(obj):
    return obj.__class__ is FakeDate


def is_fake_datetime(obj):
    return obj.__class__ is FakeDatetime


def cpython_only(func):
    @wraps(func)
    def wrapper(*args):
        if not _is_cpython:
            raise skip.SkipTest("Requires CPython")
        return func(*args)
    return wrapper
