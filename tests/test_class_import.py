import sure
from .fake_module import fake_datetime_function, fake_date_function
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from datetime import datetime


@freeze_time("2012-01-14")
def test_import_datetime_works():
    fake_datetime_function().day.should.equal(14)


@freeze_time("2012-01-14")
def test_import_date_works():
    fake_date_function().day.should.equal(14)


def test_start_and_stop_works():
    freezer = freeze_time("2012-01-14")

    fake_datetime_function().should.be.a(datetime)
    fake_datetime_function().shouldnt.be.a(FakeDatetime)

    freezer.start()
    fake_datetime_function().day.should.equal(14)
    fake_datetime_function().should.be.a(datetime)
    fake_datetime_function().should.be.a(FakeDatetime)

    freezer.stop()
    fake_datetime_function().should.be.a(datetime)
    fake_datetime_function().shouldnt.a(FakeDatetime)
