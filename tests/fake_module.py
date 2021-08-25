from datetime import date, datetime
from time import gmtime, localtime, strftime, time


def fake_datetime_function():
    return datetime.now()


def fake_date_function():
    return date.today()


def fake_time_function():
    return time()


def fake_localtime_function():
    return localtime()


def fake_gmtime_function():
    return gmtime()


def fake_strftime_function():
    return strftime("%Y")


class EqualToAnything:
    description = "This is the equal_to_anything object"

    def __eq__(self, other):
        return True

    def __neq__(self, other):
        return False


equal_to_anything = EqualToAnything()
