import datetime
import uuid
from typing import Any
import pytest
import sys
from freezegun import freeze_time


def time_from_uuid(value: Any) -> datetime.datetime:
    """
    Converts an UUID(1) to it's datetime value
    """
    uvalue = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
    assert uvalue.version == 1
    return (datetime.datetime(1582, 10, 15) +
            datetime.timedelta(microseconds=uvalue.time // 10))

def time_from_uuid7(value: Any) -> datetime.datetime:
    """
    Converts an UUID(7) to it's datetime value
    """
    uvalue = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
    assert uvalue.version == 7
    # UUID as 128-bit integer
    uuid_int = uvalue.int
    
    # Extract the first 48 bits (timestamp in ms)
    timestamp_ms = uuid_int >> 80
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000)


def test_uuid1_future() -> None:
    """
    Test that we can go back in time after setting a future date.
    Normally UUID1 would disallow this, since it keeps track of
    the _last_timestamp, but we override that now.
    """
    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert time_from_uuid(uuid.uuid1()) == future_target

    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert time_from_uuid(uuid.uuid1()) == past_target


def test_uuid1_past() -> None:
    """
    Test that we can go forward in time after setting some time in the past.
    This is simply the opposite of test_uuid1_future()
    """
    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert time_from_uuid(uuid.uuid1()) == past_target

    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert time_from_uuid(uuid.uuid1()) == future_target

@pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="Only valid on Python 3.14+",
)
def test_uuid7_future() -> None:
    """
    Test that we can go back in time after setting a future date.
    Normally UUID7 would disallow this, since it keeps track of
    the _last_timestamp_v7, but we override that now.
    """
    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert time_from_uuid7(uuid.uuid7()) == future_target

    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert time_from_uuid7(uuid.uuid7()) == past_target

@pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="Only valid on Python 3.14+",
)
def test_uuid7_past() -> None:
    """
    Test that we can go forward in time after setting some time in the past.
    This is simply the opposite of test_uuid7_future()
    """
    past_target = datetime.datetime(1978, 7, 6, 23, 6, 31)
    with freeze_time(past_target):
        assert time_from_uuid7(uuid.uuid7()) == past_target

    future_target = datetime.datetime(2056, 2, 6, 14, 3, 21)
    with freeze_time(future_target):
        assert time_from_uuid7(uuid.uuid7()) == future_target

