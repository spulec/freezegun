from collections.abc import Awaitable, Callable, Iterator, Sequence
from datetime import date, datetime, timedelta
from numbers import Real
from typing import Generic, Literal, TypeVar, overload
from typing_extensions import TypeAlias

_T = TypeVar("_T")
_Freezable: TypeAlias = str | datetime | date | timedelta
_Factory = TypeVar("_Factory", bound=TickingDateTimeFactory | FrozenDateTimeFactory | StepTickTimeFactory)

class TickingDateTimeFactory:
    def __init__(self, time_to_freeze: datetime, start: datetime) -> None: ...
    def __call__(self) -> datetime: ...

class FrozenDateTimeFactory:
    def __init__(self, time_to_freeze: datetime) -> None: ...
    def __call__(self) -> datetime: ...
    def tick(self, delta: float | Real | timedelta = ...) -> None: ...
    def move_to(self, target_datetime: _Freezable | None) -> None: ...

class StepTickTimeFactory:
    def __init__(self, time_to_freeze: datetime, step_width: float) -> None: ...
    def __call__(self) -> datetime: ...
    def tick(self, delta: timedelta | None = ...) -> None: ...
    def update_step_width(self, step_width: float) -> None: ...
    def move_to(self, target_datetime: _Freezable | None) -> None: ...

class _freeze_time(Generic[_Factory]):
    def __init__(
        self,
        time_to_freeze_str: _Freezable | None,
        tz_offset: int | timedelta,
        ignore: Sequence[str],
        tick: bool,
        as_arg: bool,
        as_kwarg: str,
        auto_tick_seconds: float,
    ) -> None: ...
    @overload
    def __call__(self, func: type[_T]) -> type[_T]: ...
    @overload
    def __call__(self, func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]: ...
    @overload
    def __call__(self, func: Callable[..., _T]) -> Callable[..., _T]: ...
    def __enter__(self) -> _Factory: ...
    def __exit__(self, *args: object) -> None: ...
    def start(self) -> _Factory: ...
    def stop(self) -> None: ...
    def decorate_class(self, klass: type[_T]) -> _T: ...
    def decorate_coroutine(self, coroutine: _T) -> _T: ...
    def decorate_callable(self, func: Callable[..., _T]) -> Callable[..., _T]: ...

@overload
def freeze_time(
    time_to_freeze: _Freezable | Callable[..., _Freezable] | Iterator[_Freezable] | None = ...,
    tz_offset: int | timedelta | None = ...,
    ignore: Sequence[str] | None = ...,
    tick: bool = ...,
    as_arg: bool = ...,
    as_kwarg: str = ...,
    *,
    auto_tick_seconds: float,
) -> _freeze_time[StepTickTimeFactory]: ...

@overload
def freeze_time(
    time_to_freeze: _Freezable | Callable[..., _Freezable] | Iterator[_Freezable] | None = ...,
    tz_offset: int | timedelta | None = ...,
    ignore: Sequence[str] | None = ...,
    as_arg: bool = ...,
    as_kwarg: str = ...,
    auto_tick_seconds: None = ...,
    *,
    tick: Literal[True],
) -> _freeze_time[TickingDateTimeFactory]: ...

@overload
def freeze_time(
    time_to_freeze: _Freezable | Callable[..., _Freezable] | Iterator[_Freezable] | None = ...,
    tz_offset: int | timedelta | None = ...,
    ignore: Sequence[str] | None = ...,
    tick: bool = ...,
    as_arg: bool = ...,
    as_kwarg: str = ...,
    auto_tick_seconds: None = ...,
) -> _freeze_time[FrozenDateTimeFactory]: ...
