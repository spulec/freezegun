from freezegun.api import FakeDate, FakeDatetime


def is_fake_date(obj):
    return obj.__class__ is FakeDate


def is_fake_datetime(obj):
    return obj.__class__ is FakeDatetime
