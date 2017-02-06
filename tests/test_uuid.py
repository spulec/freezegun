import datetime
import uuid

from freezegun import freeze_time


def time_from_uuid(value):
    """Converts an UUID(1) to it's datetime value"""
    uvalue = value if isinstance(value, uuid.UUID) else uuid.UUID(value)

    assert uvalue.version == 1

    return (datetime.datetime(1582, 10, 15) +
            datetime.timedelta(microseconds=uvalue.time // 10))

def test_uuid1():
    # Test that the uuid.uuid1() methods generate a value from the freezed date
    # This was not always the case as python is
    # using the system's one if available through ctypes
    target = datetime.datetime(2017, 2, 6, 14, 8, 21)

    with freeze_time(target):
        assert time_from_uuid(uuid.uuid1()) == target

