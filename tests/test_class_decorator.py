from datetime import datetime
from typing import Iterator

import pytest
from freezegun import freeze_time
from freezegun.api import FakeDatetime

@freeze_time("2022-10-01")
class TestClassDecoratorWithFixture:
    @pytest.fixture
    def ff(self) -> datetime:
        return datetime.now()

    @pytest.fixture
    def yield_ff(self) -> Iterator[datetime]:
        yield datetime.now()

    def test_with_fixture(self, ff: datetime) -> None:
        assert ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_without_fixture(self) -> None:
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_with_yield_fixture(self, yield_ff: datetime) -> None:
        assert yield_ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)
