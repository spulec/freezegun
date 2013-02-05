from freezegun import freeze_time
import time


def test_simple_api():
    freezer = freeze_time("2012-01-14")
    freezer.start()
    assert time.time() == 1326499200
    freezer.stop()
    assert time.time() != 1326499200
