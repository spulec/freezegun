from functools import wraps
from unittest import SkipTest

from freezegun.api import FakeDate, FakeDatetime, _is_cpython

import pytest


def is_fake_date(obj):
    return obj.__class__ is FakeDate


def is_fake_datetime(obj):
    return obj.__class__ is FakeDatetime


cpython_only_mark = pytest.mark.skipif(
    not _is_cpython,
    reason="Requires CPython")


def cpython_only(func):
    @wraps(func)
    def wrapper(*args):
        if not _is_cpython:
            raise SkipTest("Requires CPython")
        return func(*args)
    return wrapper
