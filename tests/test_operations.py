import datetime
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta


@freeze_time("2012-01-14")
def test_addition():
    now = datetime.datetime.now()
    later = now + datetime.timedelta(days=1)
    other_later = now + relativedelta(days=1)
    assert isinstance(later, datetime.datetime)
    assert isinstance(other_later, datetime.datetime)

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    other_tomorrow = today + relativedelta(days=1)
    assert isinstance(tomorrow, datetime.date)
    assert isinstance(other_tomorrow, datetime.date)


@freeze_time("2012-01-14")
def test_subtraction():
    now = datetime.datetime.now()
    before = now - datetime.timedelta(days=1)
    other_before = now - relativedelta(days=1)
    how_long = now - before
    assert isinstance(before, datetime.datetime)
    assert isinstance(other_before, datetime.datetime)
    assert isinstance(how_long, datetime.timedelta)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    other_yesterday = today - relativedelta(days=1)
    how_long = today - yesterday
    assert isinstance(yesterday, datetime.date)
    assert isinstance(other_yesterday, datetime.date)
    assert isinstance(how_long, datetime.timedelta)
