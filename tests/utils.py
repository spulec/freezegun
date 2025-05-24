from functools import wraps
from typing import Any, Callable, TYPE_CHECKING, TypeVar
from unittest import SkipTest

from freezegun.api import FakeDate, FakeDatetime, _is_cpython

import pytest

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")

T = TypeVar("T")


def is_fake_date(obj: Any) -> bool:
    return obj.__class__ is FakeDate


def is_fake_datetime(obj: Any) -> bool:
    return obj.__class__ is FakeDatetime


cpython_only_mark = pytest.mark.skipif(
    not _is_cpython,
    reason="Requires CPython")


def cpython_only(func: "Callable[P, T]") -> "Callable[P, T]":
    @wraps(func)
    def wrapper(*args: "P.args", **kwargs: "P.kwargs") -> T:
        if not _is_cpython:
            raise SkipTest("Requires CPython")
        return func(*args, **kwargs)
    return wrapper
