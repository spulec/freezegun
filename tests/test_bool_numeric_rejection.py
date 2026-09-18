"""bool subclasses int/numbers.Integral; True must not silently become 1s."""
from datetime import datetime, timedelta

import pytest

from freezegun import freeze_time
from freezegun.api import (
    FrozenDateTimeFactory,
    StepTickTimeFactory,
    TickingDateTimeFactory,
)


@pytest.mark.parametrize("value", [True, False])
def test_frozen_tick_rejects_bool(value: bool) -> None:
    factory = FrozenDateTimeFactory(datetime(2020, 1, 1, 12, 0, 0))
    with pytest.raises(TypeError, match="delta"):
        factory.tick(value)


@pytest.mark.parametrize("value", [True, False])
def test_ticking_tick_rejects_bool(value: bool) -> None:
    factory = TickingDateTimeFactory(
        datetime(2020, 1, 1, 12, 0, 0), datetime(2020, 1, 1, 12, 0, 0)
    )
    with pytest.raises(TypeError, match="delta"):
        factory.tick(value)


@pytest.mark.parametrize("value", [True, False])
def test_step_tick_rejects_bool(value: bool) -> None:
    factory = StepTickTimeFactory(datetime(2020, 1, 1, 12, 0, 0), 1.0)
    with pytest.raises(TypeError, match="delta"):
        factory.tick(value)


@pytest.mark.parametrize("value", [True, False])
def test_update_step_width_rejects_bool(value: bool) -> None:
    factory = StepTickTimeFactory(datetime(2020, 1, 1, 12, 0, 0), 1.0)
    with pytest.raises(TypeError, match="step_width"):
        factory.update_step_width(value)


@pytest.mark.parametrize("value", [True, False])
def test_freeze_time_auto_tick_seconds_rejects_bool(value: bool) -> None:
    with pytest.raises(TypeError, match="auto_tick_seconds"):
        freeze_time("2020-01-01", auto_tick_seconds=value)


def test_tick_still_accepts_int_and_timedelta() -> None:
    with freeze_time("2020-01-01") as frozen:
        assert frozen.tick(2) == datetime(2020, 1, 1, 0, 0, 2)
        assert frozen.tick(timedelta(seconds=3)) == datetime(2020, 1, 1, 0, 0, 5)


def test_auto_tick_seconds_still_accepts_int() -> None:
    with freeze_time("2020-01-01", auto_tick_seconds=2):
        t1 = datetime.now()
        t2 = datetime.now()
        assert (t2 - t1).total_seconds() == 2.0
