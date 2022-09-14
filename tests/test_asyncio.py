import asyncio
import datetime

from freezegun import freeze_time


def test_datetime_in_coroutine():
    @freeze_time('1970-01-01')
    async def frozen_coroutine():
        assert datetime.date.today() == datetime.date(1970, 1, 1)

    asyncio.run(frozen_coroutine())
