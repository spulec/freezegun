import contextlib
import datetime
import sys
import types
import warnings

from freezegun import freeze_time


class ModuleWithWarning(object):
    """
    A module that triggers warnings on attribute access.

    This does not happen with regular modules, there has to be a bit of lazy
    module magic going on in order for this to happen.

    Examples of modules that uses this pattern in real projects can be found at:

    py.code - the compiler package import causes a warning to be emitted:
    https://github.com/pytest-dev/py/blob/67987e26aadddbbe7d1ec76c16ea9be346ae9811/py/__init__.py
    https://github.com/pytest-dev/py/blob/67987e26aadddbbe7d1ec76c16ea9be346ae9811/py/_code/_assertionold.py#L3

    celery.task - the sets module is listed in __all__ in celery.task and freeze_time accesses it:
    https://github.com/celery/celery/blob/46c92025cdec07a4a30ad44901cf66cb27346638/celery/task/__init__.py
    https://github.com/celery/celery/blob/46c92025cdec07a4a30ad44901cf66cb27346638/celery/task/sets.py
    """
    __name__ = 'module_with_warning'
    __dict__ = {}
    warning_triggered = False
    counter = 0

    @property
    def attribute_that_emits_a_warning(self):
        # Use unique warning messages to avoid messages being only reported once
        self.__class__.counter += 1
        warnings.warn('this is test warning #{counter}'.format(counter=self.__class__.counter))
        self.warning_triggered = True


@contextlib.contextmanager
def assert_module_with_emitted_warning():
    """Install a module that triggers warnings into sys.modules and ensure the
    warning was triggered in the with-block.  """
    module = sys.modules['module_with_warning'] = ModuleWithWarning()

    try:
        yield
    finally:
        del sys.modules['module_with_warning']

    assert module.warning_triggered


@contextlib.contextmanager
def assert_no_warnings():
    """A context manager that makes sure no warnings was emitted."""
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.filterwarnings('always')
        yield
        assert not caught_warnings


def test_ignore_warnings_in_start():
    """Make sure that modules being introspected in start() does not emit warnings."""
    with assert_module_with_emitted_warning():
        freezer = freeze_time(datetime.datetime(2016, 10, 27, 9, 56))

        try:
            with assert_no_warnings():
                freezer.start()

        finally:
            freezer.stop()


def test_ignore_warnings_in_stop():
    """Make sure that modules that was loaded after start() does not trigger
    warnings in stop()"""
    freezer = freeze_time(datetime.datetime(2016, 10, 27, 9, 56))
    freezer.start()

    with assert_module_with_emitted_warning():
        with assert_no_warnings():
            freezer.stop()
