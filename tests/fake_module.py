from datetime import date, datetime
from time import time, localtime, gmtime, strftime, struct_time
from typing import Any


def fake_datetime_function() -> datetime:
    return datetime.now()


def fake_date_function() -> date:
    return date.today()


def fake_time_function() -> float:
    return time()


def fake_localtime_function() -> struct_time:
    return localtime()


def fake_gmtime_function() -> struct_time:
    return gmtime()


def fake_strftime_function() -> str:
    return strftime("%Y")


class EqualToAnything:
    description = 'This is the equal_to_anything object'

    def __eq__(self, other: Any) -> bool:
        return True

    def __neq__(self, other: Any) -> bool:
        return False


equal_to_anything = EqualToAnything()
