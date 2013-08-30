from datetime import datetime
from datetime import date
from time import time


def fake_datetime_function():
    return datetime.now()


def fake_date_function():
    return date.today()


def fake_time_function():
    return time()
