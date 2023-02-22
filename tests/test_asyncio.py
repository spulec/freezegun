import asyncio
import datetime
import time

from freezegun import freeze_time


def test_datetime_in_coroutine():
    @freeze_time('1970-01-01')
    async def frozen_coroutine():
        assert datetime.date.today() == datetime.date(1970, 1, 1)

    asyncio.run(frozen_coroutine())


def test_freezing_time_in_coroutine():
    """Test calling freeze_time while executing asyncio loop."""
    async def coroutine():
        with freeze_time('1970-01-02'):
            assert time.time() == 86400
        with freeze_time('1970-01-03'):
            assert time.time() == 86400 * 2

    asyncio.run(coroutine())


def test_freezing_time_before_running_coroutine():
    """Test calling freeze_time before executing asyncio loop."""
    async def coroutine():
        assert time.time() == 86400
    with freeze_time('1970-01-02'):
        asyncio.run(coroutine())


def test_asyncio_sleeping_not_affected_by_freeze_time():
    """Test that asyncio.sleep() is not affected by `freeze_time`.

    This test ensures that despite freezing time using `freeze_time`,
    the asyncio event loop can see real monotonic time, which is required
    to make things like `asyncio.sleep()` work.
    """

    async def coroutine():
        # Sleeping with time frozen should sleep the expected duration.
        before_sleep = time.time()
        with freeze_time('1970-01-02'):
            await asyncio.sleep(0.05)
        assert 0.02 <= time.time() - before_sleep < 0.3

        # Exiting `freeze_time` the time should not break asyncio sleeping.
        before_sleep = time.time()
        await asyncio.sleep(0.05)
        assert 0.02 <= time.time() - before_sleep < 0.3

    asyncio.run(coroutine())


def test_asyncio_to_call_later_with_frozen_time():
    """Test that asyncio `loop.call_later` works with frozen time."""
    # `to_call_later` will be called by asyncio event loop and should add
    # the Unix timestamp of 1970-01-02 00:00 to the `timestamps` list.
    timestamps = []
    def to_call_later():
        timestamps.append(time.time())

    async def coroutine():
        # Schedule calling `to_call_later` in 100 ms.
        asyncio.get_running_loop().call_later(0.1, to_call_later)

        # Sleeping for 10 ms should not result in calling `to_call_later`.
        await asyncio.sleep(0.01)
        assert timestamps == []

        # But sleeping more (150 ms in this case) should call `to_call_later`
        # and we should see `timestamps` updated.
        await asyncio.sleep(0.15)
        assert timestamps == [86400]

    with freeze_time('1970-01-02'):
        asyncio.run(coroutine())
