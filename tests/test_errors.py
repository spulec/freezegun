import contextlib
import datetime
import sys

import pytest
from freezegun import freeze_time


class ModuleWithError(object):
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

    def __init__(self, error_type):
        self.error_triggered = False
        self.error_type = error_type

    def __dir__(self):
        try:
            raise self.error_type()
        finally:
            self.error_triggered = True


@contextlib.contextmanager
def assert_module_with_raised_error(error_type):
    """Install a module into sys.modules that raises an error upon invoking
    __dir__."""
    module = sys.modules['module_with_error'] = ModuleWithError(error_type)

    try:
        yield
    finally:
        del sys.modules['module_with_error']

    assert module.error_triggered


@pytest.mark.parametrize('error_type', [ImportError, TypeError])
def test_ignore_errors_in_start(error_type):
    with assert_module_with_raised_error(error_type):
        freezer = freeze_time(datetime.datetime(2019, 1, 11, 9, 34))

        try:
            freezer.start()
        finally:
            freezer.stop()
