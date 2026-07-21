from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time
from freezegun.api import datetime_to_fakedatetime, real_datetime


def test_datetime_to_fakedatetime_preserves_fold():
    tz = ZoneInfo("US/Eastern")
    # Second 01:00 on fall-back day (fold=1) via real conversion
    real = real_datetime.fromisoformat("2025-11-02T06:00:00+00:00").astimezone(tz)
    assert real.fold == 1
    fake = datetime_to_fakedatetime(real)
    assert fake.fold == real.fold
    assert fake.strftime("%H:%M %Z") == real.strftime("%H:%M %Z")


def test_astimezone_dst_fold_matches_stdlib_under_freeze():
    """Regression #596: freezegun must not collapse EST fold hour to EDT."""
    tz = ZoneInfo("US/Eastern")
    utc_keys = [f"2025-11-02T{h:02d}:00:00+00:00" for h in range(4, 9)]
    expected = [
        datetime.fromisoformat(k).astimezone(tz).strftime("%H:%M %Z") for k in utc_keys
    ]
    with freeze_time("2025-11-01 11:30:00Z"):
        got = [
            datetime.fromisoformat(k).astimezone(tz).strftime("%H:%M %Z") for k in utc_keys
        ]
    assert got == expected
    # specifically the fold hour must be EST not EDT
    assert got[2].endswith("EST")
