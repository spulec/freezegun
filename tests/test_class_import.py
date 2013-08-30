import sure
import time
from .fake_module import fake_datetime_function, fake_date_function, fake_time_function
from freezegun import freeze_time
from freezegun.api import FakeDatetime
import datetime



@freeze_time("2012-01-14")
def test_import_datetime_works():
    fake_datetime_function().day.should.equal(14)


@freeze_time("2012-01-14")
def test_import_date_works():
    fake_date_function().day.should.equal(14)


@freeze_time("2012-01-14")
def test_import_time():
    local_time = datetime.datetime(2012, 1, 14)
    utc_time = local_time - datetime.timedelta(seconds=time.timezone)
    expected_timestamp = time.mktime(utc_time.timetuple())
    fake_time_function().should.equal(expected_timestamp)


def test_start_and_stop_works():
    freezer = freeze_time("2012-01-14")

    result = fake_datetime_function()
    result.__class__.should.equal(datetime.datetime)
    result.__class__.shouldnt.equal(FakeDatetime)

    freezer.start()
    fake_datetime_function().day.should.equal(14)
    fake_datetime_function().should.be.a(datetime.datetime)
    fake_datetime_function().should.be.a(FakeDatetime)

    freezer.stop()
    result = fake_datetime_function()
    result.__class__.should.equal(datetime.datetime)
    result.__class__.shouldnt.equal(FakeDatetime)


def test_isinstance_works():
    date = datetime.date.today()
    now = datetime.datetime.now()

    freezer = freeze_time('2011-01-01')
    freezer.start()
    isinstance(date, datetime.date).should.equal(True)
    isinstance(date, datetime.datetime).should.equal(False)
    isinstance(now, datetime.datetime).should.equal(True)
    isinstance(now, datetime.date).should.equal(True)
    freezer.stop()
