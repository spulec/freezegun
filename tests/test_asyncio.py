import datetime

from freezegun import freeze_time

try:
    import asyncio
except ImportError:
    asyncio = False


if asyncio:
    def test_time_freeze_coroutine():
        @freeze_time('1970-01-01')
        async def frozen_coroutine():
            assert datetime.date.today() == datetime.date(1970, 1, 1)

        asyncio.get_event_loop().run_until_complete(frozen_coroutine())
