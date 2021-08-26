from . import config
from ._async import wrap_coroutine
import copyreg
import dateutil
import datetime
import functools
import sys
import time
import uuid
import calendar
import unittest
import platform
import warnings
import types
import inspect
from typing import (
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from dateutil import parser
from dateutil.tz import tzlocal

_T = TypeVar("_T", bound=type)
_TimeTuple = Tuple[int, int, int, int, int, int, int, int, int]
_Freezable = Union[str, datetime.date, datetime.timedelta]

try:
    from maya import MayaDT  # type: ignore
except ImportError:
    MayaDT = None

_FreezeTypes = Union[None, _Freezable, types.FunctionType, types.GeneratorType]

_EPOCH = datetime.datetime(1970, 1, 1)
_EPOCHTZ = datetime.datetime(1970, 1, 1, tzinfo=dateutil.tz.UTC)

real_time = time.time
real_localtime = time.localtime
real_gmtime = time.gmtime
real_monotonic = time.monotonic
real_perf_counter = time.perf_counter
real_strftime = time.strftime
real_date = datetime.date
real_datetime = datetime.datetime
real_date_objects = [real_time, real_localtime, real_gmtime, real_monotonic, real_perf_counter, real_strftime, real_date, real_datetime]

if sys.version_info >= (3, 7):
    real_time_ns = time.time_ns
    real_date_objects.append(real_time_ns)
    real_monotonic_ns = time.monotonic_ns
    real_date_objects.append(real_monotonic_ns)
    real_perf_counter_ns = time.perf_counter_ns
    real_date_objects.append(real_perf_counter_ns)

_real_time_object_ids = {id(obj) for obj in real_date_objects}

# time.clock is deprecated and was removed in Python 3.8
if sys.version_info < (3, 8):
    real_clock = time.clock

freeze_factories: List["FreezeFactory"] = []
tz_offsets: List[datetime.timedelta] = []
ignore_lists: List[Tuple[str, ...]] = []
tick_flags: List[bool] = []

uuid_generate_time_attr: Optional[str]
# The following uuid attributes are undocumented and platform specific so mypy
# doesn't have type information for them.
try:
    # noinspection PyUnresolvedReferences
    real_uuid_generate_time = uuid._uuid_generate_time  # type: ignore
    uuid_generate_time_attr = '_uuid_generate_time'
except AttributeError:
    # noinspection PyUnresolvedReferences
    uuid._load_system_functions()  # type: ignore
    # noinspection PyUnresolvedReferences
    real_uuid_generate_time = uuid._generate_time_safe  # type: ignore
    uuid_generate_time_attr = '_generate_time_safe'
except ImportError:
    real_uuid_generate_time = None
    uuid_generate_time_attr = None

try:
    # noinspection PyUnresolvedReferences
    real_uuid_create = uuid._UuidCreate  # type: ignore
except (AttributeError, ImportError):
    real_uuid_create = None


# keep a cache of module attributes otherwise freezegun will need to analyze too many modules all the time
_GLOBAL_MODULES_CACHE = {}


def _get_module_attributes(module: Any) -> List[Tuple[str, Any]]:
    result: List[Tuple[str, Any]] = []
    try:
        module_attributes = dir(module)
    except (ImportError, TypeError):
        return result
    for attribute_name in module_attributes:
        try:
            attribute_value = getattr(module, attribute_name)
        except (ImportError, AttributeError, TypeError):
            # For certain libraries, this can result in ImportError(_winreg) or AttributeError (celery)
            continue
        else:
            result.append((attribute_name, attribute_value))
    return result


def _setup_module_cache(module: Any) -> None:
    date_attrs = []
    all_module_attributes = _get_module_attributes(module)
    for attribute_name, attribute_value in all_module_attributes:
        if id(attribute_value) in _real_time_object_ids:
            date_attrs.append((attribute_name, attribute_value))
    _GLOBAL_MODULES_CACHE[module.__name__] = (_get_module_attributes_hash(module), date_attrs)


def _get_module_attributes_hash(module: Any) -> str:
    try:
        module_dir = dir(module)
    except (ImportError, TypeError):
        module_dir = []
    return f'{id(module)}-{hash(frozenset(module_dir))}'


def _get_cached_module_attributes(module: Any) -> List[Tuple[str, Any]]:
    module_hash, cached_attrs = _GLOBAL_MODULES_CACHE.get(module.__name__, ('0', []))
    if _get_module_attributes_hash(module) == module_hash:
        return cached_attrs

    # cache miss: update the cache and return the refreshed value
    _setup_module_cache(module)
    # return the newly cached value
    module_hash, cached_attrs = _GLOBAL_MODULES_CACHE[module.__name__]
    return cached_attrs


_is_cpython = (
    hasattr(platform, 'python_implementation') and
    platform.python_implementation().lower() == "cpython"
)


call_stack_inspection_limit = 5


def _should_use_real_time() -> bool:
    if not call_stack_inspection_limit:
        return False

    # Means stop() has already been called, so we can now return the real time
    if not ignore_lists:
        return True

    if not ignore_lists[-1]:
        return False

    frame = inspect.currentframe()
    assert frame is not None
    frame = frame.f_back
    assert frame is not None
    frame = frame.f_back
    assert frame is not None

    for _ in range(call_stack_inspection_limit):
        module_name = frame.f_globals.get('__name__')
        if module_name and module_name.startswith(ignore_lists[-1]):
            return True

        frame = frame.f_back
        if frame is None:
            break

    return False


def get_current_time() -> real_datetime:
    return freeze_factories[-1]()


def fake_time() -> float:
    if _should_use_real_time():
        return real_time()
    current_time = get_current_time()
    return calendar.timegm(current_time.timetuple()) + current_time.microsecond / 1000000.0

if sys.version_info >= (3, 7):
    def fake_time_ns() -> int:
        if _should_use_real_time():
            return real_time_ns()
        return int(int(fake_time()) * 1e9)


def fake_localtime(secs: Optional[float] = None) -> time.struct_time:
    if secs is not None:
        return real_localtime(secs)
    if _should_use_real_time():
        return real_localtime()
    shifted_time = get_current_time() - datetime.timedelta(seconds=time.timezone)
    return shifted_time.timetuple()


def fake_gmtime(secs: Optional[float] = None) -> time.struct_time:
    if secs is not None:
        return real_gmtime(secs)
    if _should_use_real_time():
        return real_gmtime()
    return get_current_time().timetuple()


def _get_fake_monotonic() -> float:
    # For monotonic timers like .monotonic(), .perf_counter(), etc
    current_time = get_current_time()
    return (
        calendar.timegm(current_time.timetuple()) +
        current_time.microsecond / 1e6
    )


def _get_fake_monotonic_ns() -> int:
    # For monotonic timers like .monotonic(), .perf_counter(), etc
    current_time = get_current_time()
    return (
        calendar.timegm(current_time.timetuple()) * 1000000 +
        current_time.microsecond
    ) * 1000


def fake_monotonic() -> float:
    if _should_use_real_time():
        return real_monotonic()

    return _get_fake_monotonic()


def fake_perf_counter() -> float:
    if _should_use_real_time():
        return real_perf_counter()

    return _get_fake_monotonic()


if sys.version_info >= (3, 7):
    def fake_monotonic_ns() -> int:
        if _should_use_real_time():
            return real_monotonic_ns()

        return _get_fake_monotonic_ns()

    def fake_perf_counter_ns() -> int:
        if _should_use_real_time():
            return real_perf_counter_ns()
        return _get_fake_monotonic_ns()


def fake_strftime(
    format: str,
    time_to_format: Optional[Union[_TimeTuple, time.struct_time]] = None
) -> str:
    if time_to_format is None:
        if not _should_use_real_time():
            time_to_format = fake_localtime()

    if time_to_format is None:
        return real_strftime(format)
    else:
        return real_strftime(format, time_to_format)


if sys.version_info < (3, 8):
    def fake_clock() -> float:
        if _should_use_real_time():
            return real_clock()

        if len(freeze_factories) == 1:
            return 0.0 if not tick_flags[-1] else real_clock()

        first_frozen_time = freeze_factories[0]()
        last_frozen_time = get_current_time()

        timedelta = (last_frozen_time - first_frozen_time)
        total_seconds = timedelta.total_seconds()

        if tick_flags[-1]:
            total_seconds += real_clock()

        return total_seconds


class FakeDateMeta(type):
    @classmethod
    def __instancecheck__(self, obj: Any) -> bool:
        return isinstance(obj, real_date)

    @classmethod
    def __subclasscheck__(cls, subclass: Any) -> bool:
        return issubclass(subclass, real_date)


def datetime_to_fakedatetime(datetime: real_datetime) -> "FakeDatetime":
    return FakeDatetime(datetime.year,
                        datetime.month,
                        datetime.day,
                        datetime.hour,
                        datetime.minute,
                        datetime.second,
                        datetime.microsecond,
                        datetime.tzinfo)


def date_to_fakedate(date: real_date) -> "FakeDate":
    return FakeDate(date.year,
                    date.month,
                    date.day)


class FakeDate(real_date, metaclass=FakeDateMeta):
    def __add__(self, other: datetime.timedelta) -> "FakeDate":
        result = real_date.__add__(self, other)
        if isinstance(result, real_date):
            return date_to_fakedate(result)
        else:
            return result

    @overload
    def __sub__(self, other: datetime.timedelta) -> "FakeDate": ...

    @overload
    def __sub__(self, other: real_date) -> datetime.timedelta: ...

    def __sub__(self, other: Union[datetime.timedelta, real_date]) -> Union["FakeDate", datetime.timedelta]:
        result = real_date.__sub__(self, other)
        if isinstance(result, real_date):
            return date_to_fakedate(result)
        else:
            return result

    @classmethod
    def today(cls) -> "FakeDate":
        result = cls._date_to_freeze() + cls._tz_offset()
        return date_to_fakedate(result)

    @staticmethod
    def _date_to_freeze() -> real_datetime:
        return get_current_time()

    @classmethod
    def _tz_offset(cls) -> datetime.timedelta:
        return tz_offsets[-1]

FakeDate.min = date_to_fakedate(real_date.min)
FakeDate.max = date_to_fakedate(real_date.max)


class FakeDatetimeMeta(FakeDateMeta):
    @classmethod
    def __instancecheck__(self, obj: Any) -> bool:
        return isinstance(obj, real_datetime)

    @classmethod
    def __subclasscheck__(cls, subclass: Any) -> bool:
        return issubclass(subclass, real_datetime)


class FakeDatetime(real_datetime, FakeDate, metaclass=FakeDatetimeMeta):
    def __add__(self, other: datetime.timedelta) -> "FakeDatetime":
        result = real_datetime.__add__(self, other)
        if isinstance(result, real_datetime):
            return datetime_to_fakedatetime(result)
        return result

    # https://github.com/python/typeshed/blob/f1da797c62e97fd955fa9a100a10edb490448a40/stdlib/datetime.pyi#L288-L291
    @overload  # type: ignore
    def __sub__(self, other: datetime.datetime) -> datetime.timedelta: ...

    @overload
    def __sub__(self, other: datetime.timedelta) -> "FakeDatetime": ...

    def __sub__(self, other: Union[datetime.datetime, datetime.timedelta]) -> Union[datetime.timedelta, "FakeDatetime"]:
        result = real_datetime.__sub__(self, other)
        if isinstance(result, real_datetime):
            return datetime_to_fakedatetime(result)
        else:
            return result

    def astimezone(self, tz: Optional[datetime.tzinfo] = None) -> "FakeDatetime":
        if tz is None:
            tz = tzlocal()
        return datetime_to_fakedatetime(real_datetime.astimezone(self, tz))

    @classmethod
    def fromtimestamp(cls, t: float, tz: Optional[datetime.tzinfo] = None) -> "FakeDatetime":
        if tz is None:
            result = real_datetime.fromtimestamp(
                    t, tz=dateutil.tz.tzoffset("freezegun", cls._tz_offset())
                ).replace(tzinfo=None)
        else:
            result = real_datetime.fromtimestamp(t, tz)
        return datetime_to_fakedatetime(result)

    def timestamp(self) -> float:
        if self.tzinfo is None:
            return (self - _EPOCH - self._tz_offset()).total_seconds()
        return (self - _EPOCHTZ).total_seconds()

    @classmethod
    def now(cls, tz: Optional[datetime.tzinfo] = None) -> "FakeDatetime":
        now = cls._time_to_freeze() or real_datetime.now()
        if tz:
            result = tz.fromutc(now.replace(tzinfo=tz)) + cls._tz_offset()
        else:
            result = now + cls._tz_offset()
        return datetime_to_fakedatetime(result)

    def date(self) -> FakeDate:
        return date_to_fakedate(self)

    @property
    def nanosecond(self) -> int:
        # nanosecond is not a real property of stdlib datetime.
        try:
            # noinspection PyUnresolvedReferences
            return real_datetime.nanosecond  # type: ignore
        except AttributeError:
            return 0

    @classmethod
    def today(cls) -> "FakeDatetime":
        return cls.now(tz=None)

    @classmethod
    def utcnow(cls) -> "FakeDatetime":
        result = cls._time_to_freeze() or real_datetime.utcnow()
        return datetime_to_fakedatetime(result)

    @staticmethod
    def _time_to_freeze() -> Optional[real_datetime]:
        return get_current_time() if freeze_factories else None

    @classmethod
    def _tz_offset(cls) -> datetime.timedelta:
        return tz_offsets[-1]


FakeDatetime.min = datetime_to_fakedatetime(real_datetime.min)
FakeDatetime.max = datetime_to_fakedatetime(real_datetime.max)


def convert_to_timezone_naive(time_to_freeze: real_datetime) -> real_datetime:
    """
    Converts a potentially timezone-aware datetime to be a naive UTC datetime
    """
    offset = time_to_freeze.utcoffset()
    if offset is not None:
        time_to_freeze -= offset
        time_to_freeze = time_to_freeze.replace(tzinfo=None)
    return time_to_freeze


def pickle_fake_date(datetime_: FakeDate) -> Tuple[Type[FakeDate], Tuple[int, int, int]]:
    # A pickle function for FakeDate
    return FakeDate, (
        datetime_.year,
        datetime_.month,
        datetime_.day,
    )


def pickle_fake_datetime(datetime_: FakeDatetime)  -> Tuple[Type[FakeDatetime], Tuple[int, int, int, int, int, int, int, Optional[datetime.tzinfo]]]:
    # A pickle function for FakeDatetime
    return FakeDatetime, (
        datetime_.year,
        datetime_.month,
        datetime_.day,
        datetime_.hour,
        datetime_.minute,
        datetime_.second,
        datetime_.microsecond,
        datetime_.tzinfo,
    )


def _parse_time_to_freeze(time_to_freeze_str: Optional[_Freezable]) -> real_datetime:
    """Parses all the possible inputs for freeze_time
    :returns: a naive ``datetime.datetime`` object
    """
    if time_to_freeze_str is None:
        time_to_freeze_str = datetime.datetime.utcnow()

    if isinstance(time_to_freeze_str, datetime.datetime):
        time_to_freeze = time_to_freeze_str
    elif isinstance(time_to_freeze_str, datetime.date):
        time_to_freeze = datetime.datetime.combine(time_to_freeze_str, datetime.time())
    elif isinstance(time_to_freeze_str, datetime.timedelta):
        time_to_freeze = datetime.datetime.utcnow() + time_to_freeze_str
    else:
        time_to_freeze = parser.parse(time_to_freeze_str)

    return convert_to_timezone_naive(time_to_freeze)


def _parse_tz_offset(tz_offset: Union[float, datetime.timedelta]) -> datetime.timedelta:
    if isinstance(tz_offset, datetime.timedelta):
        return tz_offset
    else:
        return datetime.timedelta(hours=tz_offset)


class FreezeFactory:
    def __call__(self) -> real_datetime: ...


class TickingDateTimeFactory(FreezeFactory):

    def __init__(self, time_to_freeze: real_datetime, start: real_datetime) -> None:
        self.time_to_freeze = time_to_freeze
        self.start = start

    def __call__(self) -> real_datetime:
        return self.time_to_freeze + (real_datetime.now() - self.start)


class FrozenDateTimeFactory(FreezeFactory):

    def __init__(self, time_to_freeze: real_datetime) -> None:
        self.time_to_freeze = time_to_freeze

    def __call__(self) -> real_datetime:
        return self.time_to_freeze

    def tick(self, delta: Union[float, datetime.timedelta] = datetime.timedelta(seconds=1)) -> None:
        if not isinstance(delta, datetime.timedelta):
            delta = datetime.timedelta(seconds=delta)
        self.time_to_freeze += delta

    def move_to(self, target_datetime: Optional[_Freezable]) -> None:
        """Moves frozen date to the given ``target_datetime``"""
        target_datetime = _parse_time_to_freeze(target_datetime)
        delta = target_datetime - self.time_to_freeze
        self.tick(delta=delta)


class StepTickTimeFactory(FreezeFactory):

    def __init__(self, time_to_freeze: real_datetime, step_width: float) -> None:
        self.time_to_freeze = time_to_freeze
        self.step_width = step_width

    def __call__(self) -> real_datetime:
        return_time = self.time_to_freeze
        self.tick()
        return return_time

    def tick(self, delta: Optional[datetime.timedelta] = None) -> None:
        if not delta:
            delta = datetime.timedelta(seconds=self.step_width)
        self.time_to_freeze += delta

    def update_step_width(self, step_width: float) -> None:
        self.step_width = step_width

    def move_to(self, target_datetime: Optional[_Freezable]) -> None:
        """Moves frozen date to the given ``target_datetime``"""
        target_datetime = _parse_time_to_freeze(target_datetime)
        delta = target_datetime - self.time_to_freeze
        self.tick(delta=delta)


class _freeze_time:

    def __init__(
        self,
        time_to_freeze_str: Optional[_Freezable],
        tz_offset: float,
        ignore: Sequence[str],
        tick: bool,
        as_arg: bool,
        as_kwarg: str,
        auto_tick_seconds: float,
    ) -> None:
        self.time_to_freeze = _parse_time_to_freeze(time_to_freeze_str)
        self.tz_offset = _parse_tz_offset(tz_offset)
        self.ignore = tuple(ignore)
        self.tick = tick
        self.auto_tick_seconds = auto_tick_seconds
        self.undo_changes: List[Tuple[Any, str, Any]] = []
        self.modules_at_start: Set[str] = set()
        self.as_arg = as_arg
        self.as_kwarg = as_kwarg

    def __call__(
        self,
        func: Union[_T, Callable[..., Awaitable[_T]], Callable[..., _T]],
    ) -> Union[_T, Callable[..., Awaitable[_T]], Callable[..., _T]]:
        if isinstance(func, type):
            return self.decorate_class(func)
        elif inspect.iscoroutinefunction(func):
            func = cast(Callable[..., Awaitable[_T]], func)
            return self.decorate_coroutine(func)
        func = cast(Callable[..., _T], func)
        return self.decorate_callable(func)

    def decorate_class(self, klass: _T) -> _T:
        if issubclass(klass, unittest.TestCase):
            # If it's a TestCase, we assume you want to freeze the time for the
            # tests, from setUpClass to tearDownClass

            orig_setUpClass = klass.setUpClass
            orig_tearDownClass = klass.tearDownClass

            # https://github.com/python/mypy/issues/1006
            @classmethod  # type: ignore
            def setUpClass(cls: Type[unittest.TestCase]) -> None:
                self.start()
                if orig_setUpClass is not None:
                    orig_setUpClass()

            # https://github.com/python/mypy/issues/1006
            @classmethod  # type: ignore
            def tearDownClass(cls: Type[unittest.TestCase]) -> None:
                if orig_tearDownClass is not None:
                    orig_tearDownClass()
                self.stop()

            # https://github.com/python/mypy/issues/2427
            klass.setUpClass = setUpClass  # type: ignore
            klass.tearDownClass = tearDownClass  # type: ignore

        else:

            seen = set()

            klasses = klass.mro()
            for base_klass in klasses:
                for (attr, attr_value) in base_klass.__dict__.items():
                    if attr.startswith('_') or attr in seen:
                        continue
                    seen.add(attr)

                    if not callable(attr_value) or inspect.isclass(attr_value):
                        continue

                    try:
                        setattr(klass, attr, self(attr_value))
                    except (AttributeError, TypeError):
                        # Sometimes we can't set this for built-in types and custom callables
                        continue

        # https://github.com/python/mypy/issues/10817
        return klass  # type: ignore

    def __enter__(self) -> Any:
        return self.start()

    def __exit__(self, *args: Any) -> None:
        self.stop()

    def start(self) -> FreezeFactory:
        freeze_factory: FreezeFactory
        if self.auto_tick_seconds:
            freeze_factory = StepTickTimeFactory(self.time_to_freeze, self.auto_tick_seconds)
        elif self.tick:
            freeze_factory = TickingDateTimeFactory(self.time_to_freeze, real_datetime.now())
        else:
            freeze_factory = FrozenDateTimeFactory(self.time_to_freeze)

        is_already_started = len(freeze_factories) > 0
        freeze_factories.append(freeze_factory)
        tz_offsets.append(self.tz_offset)
        ignore_lists.append(self.ignore)
        tick_flags.append(self.tick)

        if is_already_started:
            return freeze_factory

        # Change the modules
        # https://github.com/python/mypy/issues/1152
        datetime.datetime = FakeDatetime  # type: ignore
        datetime.date = FakeDate  # type: ignore

        time.time = fake_time
        time.monotonic = fake_monotonic
        time.perf_counter = fake_perf_counter
        time.localtime = fake_localtime
        time.gmtime = fake_gmtime
        # fake_strftime has type:
        # "Callable[[str, _TimeTuple | struct_time | None], str]",
        # time.strftime has type:
        # "Callable[[str, _TimeTuple | struct_time], str]"
        #
        # The 2nd argument of fake_strftime shouldn't really accept None but
        # does as a convenient implementation detail.
        time.strftime = fake_strftime  # type: ignore
        if uuid_generate_time_attr:
            setattr(uuid, uuid_generate_time_attr, None)
        uuid._UuidCreate = None  # type: ignore
        uuid._last_timestamp = None  # type: ignore

        # https://github.com/python/typeshed/pull/5959
        copyreg.dispatch_table[real_datetime] = pickle_fake_datetime  # type: ignore
        copyreg.dispatch_table[real_date] = pickle_fake_date  # type: ignore

        # Change any place where the module had already been imported
        to_patch: List[Tuple[str, Callable[..., Any], Callable[..., Any]]] = [
            ('real_date', real_date, FakeDate),
            ('real_datetime', real_datetime, FakeDatetime),
            ('real_gmtime', real_gmtime, fake_gmtime),
            ('real_localtime', real_localtime, fake_localtime),
            ('real_monotonic', real_monotonic, fake_monotonic),
            ('real_perf_counter', real_perf_counter, fake_perf_counter),
            ('real_strftime', real_strftime, fake_strftime),
            ('real_time', real_time, fake_time),
        ]

        if sys.version_info >= (3, 7):
            time.time_ns = fake_time_ns
            to_patch.append(('real_time_ns', real_time_ns, fake_time_ns))
            time.monotonic_ns = fake_monotonic_ns
            to_patch.append(('real_monotonic_ns', real_monotonic_ns, fake_monotonic_ns))
            time.perf_counter_ns = fake_perf_counter_ns
            to_patch.append(('real_perf_counter_ns', real_perf_counter_ns, fake_perf_counter_ns))

        if sys.version_info < (3, 8):
            # time.clock is deprecated and was removed in Python 3.8
            time.clock = fake_clock
            to_patch.append(('real_clock', real_clock, fake_clock))

        self.fake_names = tuple(fake.__name__ for real_name, real, fake in to_patch)
        self.reals = {id(fake): real for real_name, real, fake in to_patch}
        fakes = {id(real): fake for real_name, real, fake in to_patch}
        add_change = self.undo_changes.append

        # Save the current loaded modules
        self.modules_at_start = set(sys.modules.keys())

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')

            for mod_name, module in list(sys.modules.items()):
                if mod_name is None or module is None or mod_name == __name__:
                    continue
                elif mod_name.startswith(self.ignore) or mod_name.endswith('.six.moves'):
                    continue
                elif (not hasattr(module, "__name__") or module.__name__ in ('datetime', 'time')):
                    continue

                module_attrs = _get_cached_module_attributes(module)
                for attribute_name, attribute_value in module_attrs:
                    fake = fakes.get(id(attribute_value))
                    if fake:
                        setattr(module, attribute_name, fake)
                        add_change((module, attribute_name, attribute_value))

        return freeze_factory

    def stop(self) -> None:
        freeze_factories.pop()
        ignore_lists.pop()
        tick_flags.pop()
        tz_offsets.pop()

        if not freeze_factories:
            # https://github.com/python/mypy/issues/1152
            datetime.datetime = real_datetime  # type: ignore
            datetime.date = real_date  # type: ignore
            # https://github.com/python/typeshed/pull/5959
            copyreg.dispatch_table.pop(real_datetime)  # type: ignore
            copyreg.dispatch_table.pop(real_date)  # type: ignore
            for module, module_attribute, original_value in self.undo_changes:
                setattr(module, module_attribute, original_value)
            self.undo_changes = []

            # Restore modules loaded after start()
            modules_to_restore = set(sys.modules.keys()) - self.modules_at_start
            self.modules_at_start = set()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                for mod_name in modules_to_restore:
                    module = sys.modules.get(mod_name, None)
                    if mod_name is None or module is None:
                        continue
                    elif mod_name.startswith(self.ignore) or mod_name.endswith('.six.moves'):
                        continue
                    elif not hasattr(module, "__name__") or module.__name__ in ('datetime', 'time'):
                        continue
                    for module_attribute in dir(module):

                        if module_attribute in self.fake_names:
                            continue
                        try:
                            attribute_value = getattr(module, module_attribute)
                        except (ImportError, AttributeError, TypeError):
                            # For certain libraries, this can result in ImportError(_winreg) or AttributeError (celery)
                            continue

                        real = self.reals.get(id(attribute_value))
                        if real:
                            setattr(module, module_attribute, real)

            time.time = real_time
            time.monotonic = real_monotonic
            time.perf_counter = real_perf_counter
            time.gmtime = real_gmtime
            time.localtime = real_localtime
            time.strftime = real_strftime
            if sys.version_info < (3, 8):
                time.clock = real_clock

            if sys.version_info >= (3, 7):
                time.time_ns = real_time_ns
                time.monotonic_ns = real_monotonic_ns
                time.perf_counter_ns = real_perf_counter_ns

            if uuid_generate_time_attr:
                setattr(uuid, uuid_generate_time_attr, real_uuid_generate_time)
            uuid._UuidCreate = real_uuid_create  # type: ignore
            uuid._last_timestamp = None  # type: ignore

    def decorate_coroutine(self, coroutine: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
        return wrap_coroutine(self, coroutine)

    def decorate_callable(self, func: Callable[..., _T]) -> Callable[..., _T]:
        def wrapper(*args: Any, **kwargs: Any) -> _T:
            with self as time_factory:
                if self.as_arg and self.as_kwarg:
                    assert False, "You can't specify both as_arg and as_kwarg at the same time. Pick one."
                elif self.as_arg:
                    result = func(time_factory, *args, **kwargs)
                elif self.as_kwarg:
                    kwargs[self.as_kwarg] = time_factory
                    result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)

        return wrapper


def freeze_time(
    time_to_freeze: _FreezeTypes = None,
    tz_offset: float = 0,
    ignore: Optional[List[str]] = None,
    tick: bool = False,
    as_arg: bool = False,
    as_kwarg: str = '',
    auto_tick_seconds: float = 0,
) -> _freeze_time:
    acceptable_times: Tuple[type, ...] = (type(None), str, datetime.date, datetime.timedelta,
             types.FunctionType, types.GeneratorType)

    if MayaDT is not None:
        acceptable_times += MayaDT,

    if not isinstance(time_to_freeze, acceptable_times):
        raise TypeError(('freeze_time() expected None, a string, date instance, datetime '
                         'instance, MayaDT, timedelta instance, function or a generator, but got '
                         'type {}.').format(type(time_to_freeze)))
    if tick and not _is_cpython:
        raise SystemError('Calling freeze_time with tick=True is only compatible with CPython')

    if isinstance(time_to_freeze, types.FunctionType):
        return freeze_time(time_to_freeze(), tz_offset, ignore, tick, as_arg, as_kwarg, auto_tick_seconds)

    if isinstance(time_to_freeze, types.GeneratorType):
        return freeze_time(next(time_to_freeze), tz_offset, ignore, tick, as_arg, as_kwarg, auto_tick_seconds)

    if MayaDT is not None and isinstance(time_to_freeze, MayaDT):
        return freeze_time(time_to_freeze.datetime(), tz_offset, ignore,
                           tick, as_arg, as_kwarg, auto_tick_seconds)

    assert time_to_freeze is None or isinstance(time_to_freeze, (str, datetime.date, datetime.timedelta))

    if ignore is None:
        ignore = []
    ignore = ignore[:]
    if config.settings.default_ignore_list:
        ignore.extend(config.settings.default_ignore_list)

    return _freeze_time(
        time_to_freeze_str=time_to_freeze,
        tz_offset=tz_offset,
        ignore=ignore,
        tick=tick,
        as_arg=as_arg,
        as_kwarg=as_kwarg,
        auto_tick_seconds=auto_tick_seconds,
    )


# Setup adapters for sqlite
try:
    # noinspection PyUnresolvedReferences
    import sqlite3
except ImportError:
    # Some systems have trouble with this
    pass
else:
    # These are copied from Python sqlite3.dbapi2
    def adapt_date(val: FakeDate) -> str:
        return val.isoformat()

    def adapt_datetime(val: FakeDatetime) -> str:
        return val.isoformat(" ")

    sqlite3.register_adapter(FakeDate, adapt_date)
    sqlite3.register_adapter(FakeDatetime, adapt_datetime)


# Setup converters for pymysql
try:
    import pymysql.converters
except ImportError:
    pass
else:
    pymysql.converters.encoders[FakeDate] = pymysql.converters.encoders[real_date]
    pymysql.converters.conversions[FakeDate] = pymysql.converters.encoders[real_date]
    pymysql.converters.encoders[FakeDatetime] = pymysql.converters.encoders[real_datetime]
    pymysql.converters.conversions[FakeDatetime] = pymysql.converters.encoders[real_datetime]
