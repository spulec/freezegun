from freezegun import freeze_time
from datetime import datetime


@freeze_time("2012-01-14")
def test():
    assert datetime.now() == datetime(2012, 1, 14)
