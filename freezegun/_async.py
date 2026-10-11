import functools
from typing import Any, Callable, TypeVar, cast


_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


def wrap_coroutine(api: Any, coroutine: _CallableT) -> _CallableT:
    @functools.wraps(coroutine)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        with api as time_factory:
            result = await api._call_with_time_factory(time_factory, func=coroutine, args=args, kwargs=kwargs)
        return result

    return cast(_CallableT, wrapper)
