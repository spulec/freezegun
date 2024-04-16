from datetime import date, datetime
from time import time, localtime, gmtime, strftime
from typing import Any

from freezegun.api import (
    FakeDatetime,
    FakeDate,
    fake_time,
    fake_localtime,
    fake_gmtime,
    fake_strftime,
)


# Reals

def get_datetime() -> Any:
    return datetime


def get_date() -> Any:
    return date


def get_time() -> Any:
    return time


def get_localtime() -> Any:
    return localtime


def get_gmtime() -> Any:
    return gmtime


def get_strftime() -> Any:
    return strftime


# Fakes

def get_fake_datetime() -> Any:
    return FakeDatetime


def get_fake_date() -> Any:
    return FakeDate


def get_fake_time() -> Any:
    return fake_time


def get_fake_localtime() -> Any:
    return fake_localtime


def get_fake_gmtime() -> Any:
    return fake_gmtime


def get_fake_strftime() -> Any:
    return fake_strftime
