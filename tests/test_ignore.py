import calendar
import datetime
import sys
import time
import types
from typing import Callable

import pytest

from freezegun import configure, freeze_time
from freezegun.config import reset_config


def setup_function() -> None:
    reset_config()


def teardown_function() -> None:
    reset_config()


@pytest.fixture
def clock_module(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], types.ModuleType]:
    def create(name: str) -> types.ModuleType:
        module = types.ModuleType(name)
        exec(
            'from datetime import datetime as datetime_aliased\n'
            'import time\n'
            'def read_datetime():\n'
            '    return datetime_aliased.now()\n'
            'def read_time():\n'
            '    return time.time()\n',
            module.__dict__,
        )
        monkeypatch.setitem(sys.modules, name, module)
        return module

    return create


@pytest.mark.parametrize('module_name', [
    'gitlab', 'gitlab_my_helper', 'git_module_name.minimal', 'gig', 'ordinary_module',
])
@pytest.mark.parametrize('clock', ['read_datetime', 'read_time'])
def test_default_ignore_does_not_match_unrelated_gi_prefix(
    clock_module: Callable[[str], types.ModuleType], module_name: str, clock: str,
) -> None:
    module = clock_module(module_name)
    expected_datetime = datetime.datetime(2001, 2, 3)
    expected_time = calendar.timegm(expected_datetime.timetuple())

    with freeze_time('2001-02-03'):
        assert getattr(module, clock)() == (
            expected_datetime if clock == 'read_datetime' else expected_time
        )


@pytest.mark.parametrize('module_name', ['gi', 'gi.repository'])
def test_default_ignore_preserves_gi_root_and_submodules(
    clock_module: Callable[[str], types.ModuleType], module_name: str,
) -> None:
    module = clock_module(module_name)
    real_datetime = datetime.datetime
    before = time.time()
    with freeze_time('2001-02-03'):
        assert module.datetime_aliased is real_datetime
        observed = module.read_time()
    assert before <= observed <= time.time()


@pytest.mark.parametrize('prefix,module_name', [
    ('custom', 'custom_helper'), ('gi', 'gitlab'), ('', 'ordinary_module'),
])
def test_custom_ignore_prefixes_are_preserved(
    clock_module: Callable[[str], types.ModuleType], prefix: str, module_name: str,
) -> None:
    configure(default_ignore_list=[])
    module = clock_module(module_name)
    real_datetime = datetime.datetime
    before = time.time()
    with freeze_time('2001-02-03', ignore=[prefix]):
        assert module.datetime_aliased is real_datetime
        observed = module.read_time()
    assert before <= observed <= time.time()


@pytest.mark.parametrize('module_name', ['gi', 'gi.repository'])
def test_empty_default_ignore_list_allows_gi_to_be_frozen(
    clock_module: Callable[[str], types.ModuleType], module_name: str,
) -> None:
    configure(default_ignore_list=[])
    module = clock_module(module_name)
    expected = datetime.datetime(2001, 2, 3)
    with freeze_time('2001-02-03', ignore=[]):
        assert module.read_datetime() == expected
        assert module.read_time() == calendar.timegm(expected.timetuple())


@pytest.mark.parametrize('module_name', ['gitlab', 'git_module_name.minimal', 'gig', 'ordinary_module'])
def test_unrelated_gi_prefix_imported_during_freeze_is_restored(
    clock_module: Callable[[str], types.ModuleType], module_name: str,
) -> None:
    with freeze_time('2001-02-03'):
        module = clock_module(module_name)
        assert module.read_datetime() == datetime.datetime(2001, 2, 3)
    assert module.datetime_aliased is datetime.datetime


@pytest.mark.parametrize('module_name', ['gitlab', 'gig', 'ordinary_module'])
def test_unrelated_gi_prefix_imported_during_freeze_uses_frozen_time(
    clock_module: Callable[[str], types.ModuleType], module_name: str,
) -> None:
    expected = datetime.datetime(2001, 2, 3)
    with freeze_time('2001-02-03'):
        module = clock_module(module_name)
        assert module.read_time() == calendar.timegm(expected.timetuple())


@pytest.mark.parametrize('mode', ['invocation', 'default', 'extended_default'])
@pytest.mark.parametrize('module_name', ['gi', 'gi.repository'])
def test_gi_dot_ignore_includes_root_and_submodules(
    clock_module: Callable[[str], types.ModuleType], mode: str, module_name: str,
) -> None:
    configure(default_ignore_list=[])
    if mode == 'default':
        configure(default_ignore_list=['gi.'])
    elif mode == 'extended_default':
        configure(extend_ignore_list=['gi.'])
    module = clock_module(module_name)
    real_datetime = datetime.datetime
    before = time.time()
    with freeze_time('2001-02-03', ignore=['gi.'] if mode == 'invocation' else []):
        assert module.datetime_aliased is real_datetime
        observed = module.read_time()
    assert before <= observed <= time.time()


@pytest.mark.parametrize('mode', ['default', 'extended_default'])
def test_configured_ignore_prefixes_are_preserved(
    clock_module: Callable[[str], types.ModuleType], mode: str,
) -> None:
    configure(default_ignore_list=[])
    if mode == 'default':
        configure(default_ignore_list=['gi'])
    else:
        configure(extend_ignore_list=['gi'])
    module = clock_module('gitlab')
    real_datetime = datetime.datetime
    before = time.time()
    with freeze_time('2001-02-03'):
        assert module.datetime_aliased is real_datetime
        observed = module.read_time()
    assert before <= observed <= time.time()


def test_nested_freezing_preserves_custom_prefix_and_restores_outer_ignore(
    clock_module: Callable[[str], types.ModuleType],
) -> None:
    module = clock_module('gitlab')
    outer_time = calendar.timegm(datetime.datetime(2001, 2, 3).timetuple())
    before = time.time()
    with freeze_time('2001-02-03'):
        assert module.read_time() == outer_time
        with freeze_time('2002-02-03', ignore=['gi']):
            observed = module.read_time()
        assert module.read_time() == outer_time
    assert before <= observed <= time.time()
