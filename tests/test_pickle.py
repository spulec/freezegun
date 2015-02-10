import datetime
import pickle
from freezegun import freeze_time


def assert_pickled_datetimes_equal_original():
    min_datetime = datetime.datetime.min
    max_datetime = datetime.datetime.max
    min_date = datetime.date.min
    max_date = datetime.date.max
    now = datetime.datetime.now()
    today = datetime.date.today()
    utc_now = datetime.datetime.utcnow()
    assert pickle.loads(pickle.dumps(min_datetime)) == min_datetime
    assert pickle.loads(pickle.dumps(max_datetime)) == max_datetime
    assert pickle.loads(pickle.dumps(min_date)) == min_date
    assert pickle.loads(pickle.dumps(max_date)) == max_date
    assert pickle.loads(pickle.dumps(now)) == now
    assert pickle.loads(pickle.dumps(today)) == today
    assert pickle.loads(pickle.dumps(utc_now)) == utc_now


def test_pickle():
    freezer = freeze_time("2012-01-14")

    freezer.start()
    assert_pickled_datetimes_equal_original()

    freezer.stop()
    assert_pickled_datetimes_equal_original()


def test_pickle_real_datetime():
    real_datetime = datetime.datetime(1970, 2, 1)
    pickle.loads(pickle.dumps(real_datetime)) == real_datetime

    freezer = freeze_time("1970-01-01")
    freezer.start()
    fake_datetime = datetime.datetime.now()
    assert pickle.loads(pickle.dumps(fake_datetime)) == fake_datetime
    pickle.loads(pickle.dumps(real_datetime))
    freezer.stop()

    assert pickle.loads(pickle.dumps(fake_datetime)) == fake_datetime
    assert pickle.loads(pickle.dumps(real_datetime)) == real_datetime


def test_pickle_real_date():
    real_date = datetime.date(1970, 2, 1)
    assert pickle.loads(pickle.dumps(real_date)) == real_date

    freezer = freeze_time("1970-01-01")
    freezer.start()
    fake_date = datetime.datetime.now()
    assert pickle.loads(pickle.dumps(fake_date)) == fake_date
    pickle.loads(pickle.dumps(real_date))
    freezer.stop()

    assert pickle.loads(pickle.dumps(fake_date)) == fake_date
    assert pickle.loads(pickle.dumps(real_date)) == real_date
