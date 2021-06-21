import functools
from typing import Any, Callable, TypeVar, cast

import asyncio


_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


def wrap_coroutine(api: Any, coroutine: _CallableT) -> _CallableT:
    @functools.wraps(coroutine)
    @asyncio.coroutine
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with api as time_factory:
            if api.as_arg:
                result = yield from coroutine(time_factory, *args, **kwargs)
            else:
                result = yield from coroutine(*args, **kwargs)
        return result

    return cast(_CallableT, wrapper)
