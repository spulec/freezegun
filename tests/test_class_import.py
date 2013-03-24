import sure
from .fake_module import fake_function
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from datetime import datetime


@freeze_time("2012-01-14")
def test_import_datetime_works():
    fake_function().day.should.equal(14)


def test_start_and_stop_works():
    freezer = freeze_time("2012-01-14")

    fake_function().should.be.a(datetime)
    fake_function().shouldnt.be.a(FakeDatetime)

    freezer.start()
    fake_function().day.should.equal(14)
    fake_function().should.be.a(datetime)
    fake_function().should.be.a(FakeDatetime)

    freezer.stop()
    fake_function().should.be.a(datetime)
    fake_function().shouldnt.a(FakeDatetime)
