import contextlib
import datetime
import sys
import time
import types
from typing import Any, Iterator

import pytest
from freezegun import freeze_time
from freezegun import api


class ModuleWithError:
    """
    A module that triggers an error on __dir__ access.

    This could happen with modules that overrides its __dir__ method and
    performing non standard operations.

    One such example is IPython which adds shim modules when certain packages
    are imported. (Eg. `import IPython.html`) This leads to errors upon
    activating freezegun if the modules being shimmed are not installed.

    See: https://github.com/ipython/ipython/blob/5.8.0/IPython/utils/shimmodule.py#L75
    """
    __name__ = 'module_with_error'
    __dict__ = {}

    def __init__(self, error_type: Any):
        self.error_triggered = False
        self.error_type = error_type

    def __dir__(self) -> Any:
        try:
            raise self.error_type()
        finally:
            self.error_triggered = True


@contextlib.contextmanager
def assert_module_with_raised_error(error_type: Any) -> Iterator[None]:
    """Install a module into sys.modules that raises an error upon invoking
    __dir__."""
    module = sys.modules['module_with_error'] = ModuleWithError(error_type)  # type: ignore

    try:
        yield
    finally:
        del sys.modules['module_with_error']

    assert module.error_triggered


@pytest.mark.parametrize('error_type', [ImportError, TypeError])
def test_ignore_errors_in_start(error_type: Any) -> None:
    with assert_module_with_raised_error(error_type):
        freezer = freeze_time(datetime.datetime(2019, 1, 11, 9, 34))

        try:
            freezer.start()
        finally:
            freezer.stop()


@pytest.mark.parametrize('error_type', [RuntimeError, KeyboardInterrupt])
@pytest.mark.parametrize('attribute_error', [False, True])
def test_failed_start_restores_time(error_type: Any, attribute_error: bool) -> None:
    original_date = datetime.date
    original_datetime = datetime.datetime
    original_time = time.time
    original_monotonic = time.monotonic
    module = types.ModuleType('freezegun_start_failure')
    alias = types.ModuleType('freezegun_start_alias')
    alias.date = original_date  # type: ignore[attr-defined]
    failure = error_type('module scan failed')

    def fail(*args: Any) -> Any:
        raise failure

    if attribute_error:
        module.__dir__ = lambda: ['lazy_attribute']  # type: ignore[method-assign]
        module.__getattr__ = fail  # type: ignore[method-assign]
    else:
        module.__dir__ = fail  # type: ignore[method-assign]

    # The alias must be patched before the failing module is reached.
    sys.modules[alias.__name__] = alias
    sys.modules[module.__name__] = module
    freezer = freeze_time('2000-01-01')
    try:
        with pytest.raises(error_type) as caught:
            with freezer:
                pytest.fail('the context must not be entered')
        assert caught.value is failure
        assert datetime.date is original_date
        assert datetime.datetime is original_datetime
        assert time.time is original_time
        assert time.monotonic is original_monotonic
        assert alias.date is original_date  # type: ignore[attr-defined]
        assert not api.freeze_factories
        assert not api.tz_offsets
        assert not api.ignore_lists
        assert not api.tick_flags
        assert not freezer.undo_changes
    finally:
        del sys.modules[module.__name__]
        del sys.modules[alias.__name__]
        # Keep the regression isolated even when run against the broken code.
        if api.freeze_factories:
            freezer.stop()

    # The same freezer remains usable after the failing module is removed.
    with freezer:
        assert datetime.date.today() == datetime.date(2000, 1, 1)
    assert datetime.date is original_date
