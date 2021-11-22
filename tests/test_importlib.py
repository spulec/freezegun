from datetime import datetime as from_datetime
import datetime as toplevel_datetime

from freezegun import freeze_time


def test_from_datetime():
    # Importing the datetime class doesn't work when pytest is using import-mode=importlib.
    # This is supposed to become the default, according to the documentation: https://docs.pytest.org/en/latest/changelog.html?highlight=importlib#pytest-6-0-0rc1-2020-07-08
    with freeze_time("2019-01-01"):
        assert from_datetime.utcnow().year == 2019


def test_top_level_datetime():
    # freezegun works as expected when we're importing the datetime module
    with freeze_time("2019-01-01"):
        assert toplevel_datetime.datetime.utcnow().year == 2019
