import mock
from nose.plugins import skip

from freezegun import api
from tests import utils

try:
    reload
except NameError:
    try:
        from importlib import reload
    except ImportError:
        from imp import reload


@mock.patch('platform.python_implementation', lambda: 'CPython')
def test_should_not_skip_cpython():
    reload(api)
    reload(utils)
    function_mock = mock.MagicMock(__name__='function')
    try:
        utils.cpython_only(function_mock)()
    except skip.SkipTest:
        raise AssertionError("Test was skipped in CPython")
    assert function_mock.called


@mock.patch('platform.python_implementation', lambda: 'not-CPython')
def test_should_skip_non_cpython():
    reload(api)
    reload(utils)
    function_mock = mock.MagicMock(__name__='function', skipped=False)
    try:
        utils.cpython_only(function_mock)()
    except skip.SkipTest:
        function_mock.skipped = True
    assert not function_mock.called
    assert function_mock.skipped
