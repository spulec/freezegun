import asyncio
import datetime
from textwrap import dedent
from unittest import SkipTest

from freezegun import freeze_time


def test_time_freeze_coroutine():
    if not asyncio:
        raise SkipTest('asyncio required')

    @freeze_time('1970-01-01')
    async def frozen_coroutine():
        assert datetime.date.today() == datetime.date(1970, 1, 1)

    asyncio.run(frozen_coroutine())
