import datetime
from freezegun import freeze_time
import sqlite3


@freeze_time("2013-01-01")
def test_fake_datetime_select() -> None:
    db = sqlite3.connect("/tmp/foo")
    db.execute("""select ?""", (datetime.datetime.now(),))


@freeze_time("2013-01-01")
def test_fake_date_select() -> None:
    db = sqlite3.connect("/tmp/foo")
    db.execute("""select ?""", (datetime.date.today(),))
