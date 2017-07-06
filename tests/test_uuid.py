from __future__ import print_function, absolute_import, unicode_literals
import datetime
import uuid

from nose.tools import assert_equal

from freezegun import freeze_time


def time_from_uuid(value):
    """
    Converts an UUID(1) to it's datetime value
    """
    uvalue = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
    assert uvalue.version == 1
    return (datetime.datetime(1582, 10, 15) +
            datetime.timedelta(microseconds=uvalue.time // 10))


def test_uuid1_future():
    """
    Test that we can go back in time after setting a future date.
    Normally UUID1 would disallow this, since it keeps track of
    the _last_timestamp, but we override that now.
    """
    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert_equal(time_from_uuid(uuid.uuid1()), future_target)

    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert_equal(time_from_uuid(uuid.uuid1()), past_target)


def test_uuid1_past():
    """
    Test that we can go forward in time after setting some time in the past.
    This is simply the opposite of test_uuid1_future()
    """
    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert_equal(time_from_uuid(uuid.uuid1()), past_target)

    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert_equal(time_from_uuid(uuid.uuid1()), future_target)
