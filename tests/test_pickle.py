import datetime
import pickle
from freezegun import freeze_time
import sure


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
    pickle.loads(pickle.dumps(real_datetime)).should.equal(real_datetime)

    freezer = freeze_time("1970-01-01")
    freezer.start()
    fake_datetime = datetime.datetime.now()
    pickle.loads(pickle.dumps(fake_datetime)).should.equal(fake_datetime)
    pickle.loads(pickle.dumps(real_datetime))
    freezer.stop()

    pickle.loads(pickle.dumps(fake_datetime)).should.equal(fake_datetime)
    pickle.loads(pickle.dumps(real_datetime)).should.equal(real_datetime)


def test_pickle_real_date():
    real_date = datetime.date(1970, 2, 1)
    pickle.loads(pickle.dumps(real_date)).should.equal(real_date)

    freezer = freeze_time("1970-01-01")
    freezer.start()
    fake_date = datetime.datetime.now()
    pickle.loads(pickle.dumps(fake_date)).should.equal(fake_date)
    pickle.loads(pickle.dumps(real_date))
    freezer.stop()

    pickle.loads(pickle.dumps(fake_date)).should.equal(fake_date)
    pickle.loads(pickle.dumps(real_date)).should.equal(real_date)
