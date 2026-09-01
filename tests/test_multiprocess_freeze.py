import datetime
import multiprocessing as mp
import sys
from multiprocessing.queues import Queue as MpQueue

import pytest

from freezegun import freeze_time


class _QueueProcess(mp.Process):
    def __init__(self, data_queue: "MpQueue[datetime.datetime]") -> None:
        self._data_queue = data_queue
        mp.Process.__init__(self)

    def run(self) -> None:
        self._data_queue.put(datetime.datetime.now())


pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="fork start method is unavailable on Windows"
)


def _reset_start_method() -> None:
    # Test hygiene: restore the unset state (public reset API).
    mp.set_start_method(None, force=True)


def teardown_module() -> None:
    _reset_start_method()


@freeze_time("2012-01-14")
def test_freeze_time_propagates_to_process_child() -> None:
    """Regression #593: Py3.14 default start method broke child freeze inheritance."""
    queue: "MpQueue[datetime.datetime]" = mp.Queue()
    process = _QueueProcess(queue)
    process.start()
    result = queue.get(timeout=10)
    process.join(timeout=10)
    assert result == datetime.datetime(2012, 1, 14)


def test_unset_start_method_restored_after_freeze() -> None:
    # The unset state must survive a freeze/unfreeze cycle untouched.
    assert mp.get_start_method(allow_none=True) is None
    with freeze_time("2012-01-14"):
        assert mp.get_start_method() == "fork"
    assert mp.get_start_method(allow_none=True) is None


def test_explicit_start_method_choice_is_respected() -> None:
    mp.set_start_method("forkserver")
    try:
        with freeze_time("2012-01-14"):
            assert mp.get_start_method() == "forkserver"
        assert mp.get_start_method() == "forkserver"
    finally:
        _reset_start_method()


def test_repeated_freeze_cycles_do_not_leak_state() -> None:
    for _ in range(3):
        with freeze_time("2012-01-14"):
            assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert mp.get_start_method(allow_none=True) is None
