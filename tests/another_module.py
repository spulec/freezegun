from datetime import date, datetime
from time import time, localtime, gmtime, strftime

from freezegun.api import (
    FakeDatetime,
    FakeDate,
    fake_time,
    fake_localtime,
    fake_gmtime,
    fake_strftime,
)


# Reals

def get_datetime():
    return datetime


def get_date():
    return date


def get_time():
    return time


def get_localtime():
    return localtime


def get_gmtime():
    return gmtime


def get_strftime():
    return strftime


# Fakes

def get_fake_datetime():
    return FakeDatetime


def get_fake_date():
    return FakeDate


def get_fake_time():
    return fake_time


def get_fake_localtime():
    return fake_localtime


def get_fake_gmtime():
    return fake_gmtime


def get_fake_strftime():
    return fake_strftime
