from freezegun import freeze_time
from datetime import datetime as datetime_aliased
from time import time as time_aliased


@freeze_time("1980-01-01")
def test_datetime_alias() -> None:
    assert datetime_aliased.now() == datetime_aliased(1980, 1, 1)


@freeze_time("1970-01-01")
def test_time_alias() -> None:
    assert time_aliased() == 0.0


@freeze_time('2013-04-09')
class TestCallOtherFuncInTestClassDecoratorWithAlias:

    def test_calls_other_method(self) -> None:
        assert datetime_aliased(2013, 4, 9) == datetime_aliased.today()
        self.some_other_func()
        assert datetime_aliased(2013, 4, 9) == datetime_aliased.today()

    def some_other_func(self) -> None:
        pass
