import asyncio
import functools
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

if TYPE_CHECKING:
    from .api import _freeze_time


_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


def wrap_coroutine(api: '_freeze_time', coroutine: _CallableT) -> _CallableT:
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
