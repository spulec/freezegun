from datetime import datetime
from datetime import date
from time import time


def fake_datetime_function():
    return datetime.now()


def fake_date_function():
    return date.today()


def fake_time_function():
    return time()


class EqualToAnything(object):
    description = 'This is the equal_to_anything object'

    def __eq__(self, other):
        return True

    def __neq__(self, other):
        return False


equal_to_anything = EqualToAnything()
