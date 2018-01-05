import datetime
from textwrap import dedent

from nose.plugins import skip

from freezegun import freeze_time

try:
    import asyncio
except ImportError:
    asyncio = False


def test_time_freeze_coroutine():
    if not asyncio:
        raise skip.SkipTest('asyncio required')
    @asyncio.coroutine
    @freeze_time('1970-01-01')
    def frozen_coroutine():
        assert datetime.date.today() == datetime.date(1970, 1, 1)

    asyncio.get_event_loop().run_until_complete(frozen_coroutine())


def test_time_freeze_async_def():
    try:
        exec('async def foo(): pass')
    except SyntaxError:
        raise skip.SkipTest('async def not supported')
    else:
        exec(dedent('''
        @freeze_time('1970-01-01')
        async def frozen_coroutine():
            assert datetime.date.today() == datetime.date(1970, 1, 1)
        asyncio.get_event_loop().run_until_complete(frozen_coroutine())
        '''))
