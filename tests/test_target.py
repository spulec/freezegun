import datetime
import time

import pytest

from freezegun import freeze_time
from freezegun.api import (
    Target, real_date, real_datetime, FakeDate, FakeDatetime, real_gmtime,
    fake_gmtime, real_localtime, fake_localtime, fake_monotonic, real_monotonic,
    real_strftime, fake_strftime, real_time, fake_time,
)

HAS_TIME_NS = hasattr(time, 'time_ns')
HAS_MONOTONIC_NS = hasattr(time, 'monotonic_ns')
HAS_CLOCK = hasattr(time, 'clock')

TARGETS = [
    (Target.DATE, datetime, real_date, FakeDate),
    (Target.DATETIME, datetime, real_datetime, FakeDatetime),
    (Target.GMTIME, time, real_gmtime, fake_gmtime),
    (Target.LOCALTIME, time, real_localtime, fake_localtime),
    (Target.MONOTONIC, time, real_monotonic, fake_monotonic),
    (Target.STRFTIME, time, real_strftime, fake_strftime),
    (Target.TIME, time, real_time, fake_time),
]
if HAS_TIME_NS:
    from freezegun.api import real_time_ns, fake_time_ns
    TARGETS.append((Target.TIME_NS, time, real_time_ns, fake_time_ns))
if HAS_MONOTONIC_NS:
    from freezegun.api import real_monotonic_ns, fake_monotonic_ns
    TARGETS.append((Target.MONOTONIC_NS, time, real_monotonic_ns, fake_monotonic_ns))
if HAS_CLOCK:
    from freezegun.api import real_clock, fake_clock
    TARGETS.append((Target.CLOCK, time, real_clock, fake_clock))


@pytest.mark.parametrize(
    'target_to_patch,expected',
    (
        (target, fake)
        for (target, _, _, fake) in TARGETS
    )
)
def test_target(target_to_patch, expected):
    assert TARGETS
    with freeze_time(targets={target_to_patch}):
        for target, module, real, fake in TARGETS:
            assert getattr(module, target) == (
                real if target != target_to_patch else fake
            )

    for target, module, real, fake in TARGETS:
        assert getattr(module, target) == real


def test_default_targets():
    with freeze_time():
        for target, module, real, fake in TARGETS:
            assert getattr(module, target) == (
                fake
                if target not in (Target.MONOTONIC, Target.MONOTONIC_NS)
                else real
            )

    for target, module, real, fake in TARGETS:
        assert getattr(module, target) == real
