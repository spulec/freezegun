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

    @pytest.fixture
    def func(self) -> Iterator[datetime]:
        yield datetime.now()

    def test_with_fixture(self, ff: datetime) -> None:
        assert ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_without_fixture(self) -> None:
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_with_yield_fixture(self, yield_ff: datetime) -> None:
        assert yield_ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_with_func_fixture(self, func: datetime) -> None:
        assert func == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)


@pytest.mark.parametrize("func", ("a", "b"))
@freeze_time(datetime.now())
def test_decorator_with_argument_named_func(func: str) -> None:
    """Verify that we can pass an argument called 'func'"""
    assert func in ("a", "b")


@pytest.mark.parametrize("arg", ("a", "b"))
@freeze_time(datetime.now())
def test_freezegun_with_argument_named_arg(arg: str) -> None:
    """Verify that we can pass an argument called 'arg'"""
    assert arg in ("a", "b")


@freeze_time(datetime.now())
@pytest.mark.parametrize("func", ("a", "b"))
def test_freezegun_decorator_first_parametrize_second(func: str) -> None:
    """Verify that we can pass the parametrized function into freezegun"""
    assert func in ("a", "b")
