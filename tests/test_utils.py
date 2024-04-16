from importlib import reload
from unittest import SkipTest, mock

from freezegun import api
from tests import utils


@mock.patch('platform.python_implementation', lambda: 'CPython')
def test_should_not_skip_cpython() -> None:
    reload(api)
    reload(utils)
    function_mock = mock.MagicMock(__name__='function')
    try:
        utils.cpython_only(function_mock)()
    except SkipTest:
        raise AssertionError("Test was skipped in CPython")
    assert function_mock.called


@mock.patch('platform.python_implementation', lambda: 'not-CPython')
def test_should_skip_non_cpython() -> None:
    reload(api)
    reload(utils)
    function_mock = mock.MagicMock(__name__='function', skipped=False)
    try:
        utils.cpython_only(function_mock)()
    except SkipTest:
        function_mock.skipped = True
    assert not function_mock.called
    assert function_mock.skipped
