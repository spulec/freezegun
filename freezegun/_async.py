import functools
from typing import Awaitable, Any, Callable, TypeVar, Coroutine
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")
T = TypeVar("T")


def wrap_coroutine(api: Any, coroutine: "Callable[P, Awaitable[T]]") -> "Callable[P, Coroutine[Any, Any, T]]":
    @functools.wraps(coroutine)
    async def wrapper(*args: "P.args", **kwargs: "P.kwargs") -> T:
        with api as time_factory:
            if api.as_arg:
                result = await coroutine(time_factory, *args, **kwargs)
            else:
                result = await coroutine(*args, **kwargs)
        return result

    return wrapper
