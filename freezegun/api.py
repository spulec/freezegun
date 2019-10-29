import calendar
import copyreg  # type: ignore
import datetime
import functools
import inspect
import numbers
import platform
import sys
import time
import types
import unittest
import uuid
import warnings
from typing import (
    Any, Callable, Dict, List, Mapping, Optional, Sequence,
    Set, Tuple, Type, TypeVar, Union, cast, overload
)

from dateutil import parser
from dateutil.tz import tzlocal

try:
    from maya import MayaDT as _MayaDT  # type: ignore
except ImportError:
    _MayaDT = None


_CallableT = TypeVar('_CallableT', bound=Callable[..., Any])
_TypeT = TypeVar('_TypeT', bound=Type)
_CallableOrTypeT = TypeVar('_CallableOrTypeT', bound=Union[Type, Callable[..., Any]]) 
_FactoryType = Callable[[], datetime.datetime]
_FreezeTimeInputInternalType = Union[str, datetime.date, datetime.timedelta]
_TimeTuple = Tuple[int, int, int, int, int, int, int, int, int]

_TIME_NS_PRESENT = hasattr(time, 'time_ns')

real_time = time.time
real_localtime = time.localtime
real_gmtime = time.gmtime
real_strftime = time.strftime
real_timegm = calendar.timegm
real_date = datetime.date
real_datetime = datetime.datetime
real_date_objects = [real_time, real_localtime, real_gmtime, real_strftime, real_timegm, real_date, real_datetime]

if _TIME_NS_PRESENT:
    real_time_ns = getattr(time, 'time_ns')  # type: Callable[[], int]
    real_date_objects.append(real_time_ns)

_real_time_object_ids = set(id(obj) for obj in real_date_objects)

# time.clock is deprecated and was removed in Python 3.8
real_clock = getattr(time, 'clock', None)  # type: Optional[Callable[[], float]]

freeze_factories = []  # type: List[_FactoryType]
tz_offsets = []  # type: List[datetime.timedelta]
ignore_lists = []  # type: List[Tuple[str,...]]
tick_flags = []  # type: List[bool]


try:
    # noinspection PyUnresolvedReferences
    real_uuid_generate_time = uuid._uuid_generate_time  # type: ignore
    uuid_generate_time_attr = '_uuid_generate_time'  # type: Optional[str]
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


if sys.version_info >= (3, 5):
    iscoroutinefunction = inspect.iscoroutinefunction
    from freezegun._async import wrap_coroutine
else:
    iscoroutinefunction = lambda x: False

    def wrap_coroutine(api: _freeze_time, coroutine: _CallableT) -> _CallableT:
        raise NotImplementedError()


# keep a cache of module attributes otherwise freezegun will need to analyze too many modules all the time
_GLOBAL_MODULES_CACHE = {}  # type: Dict[str, Tuple[str, List[Any]]]


def _get_module_attributes(module: types.ModuleType) -> List[Tuple[str, Any]]:
    result = []  # type: List[Tuple[str, Any]]
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


def _setup_module_cache(module: types.ModuleType) -> None:
    date_attrs = []
    all_module_attributes = _get_module_attributes(module)
    for attribute_name, attribute_value in all_module_attributes:
        if id(attribute_value) in _real_time_object_ids:
            date_attrs.append((attribute_name, attribute_value))
    _GLOBAL_MODULES_CACHE[module.__name__] = (_get_module_attributes_hash(module), date_attrs)


def _get_module_attributes_hash(module: types.ModuleType) -> str:
    try:
        module_dir = dir(module)
    except (ImportError, TypeError):
        module_dir = []
    return '{0}-{1}'.format(id(module), hash(frozenset(module_dir)))


def _get_cached_module_attributes(module: types.ModuleType) -> List[Any]:
    module_hash, cached_attrs = _GLOBAL_MODULES_CACHE.get(module.__name__, ('0', []))
    if _get_module_attributes_hash(module) == module_hash:
        return cached_attrs

    # cache miss: update the cache and return the refreshed value
    _setup_module_cache(module)
    # return the newly cached value
    module_hash, cached_attrs = _GLOBAL_MODULES_CACHE[module.__name__]
    return cached_attrs


# Stolen from six

_is_cpython = (
    hasattr(platform, 'python_implementation') and
    platform.python_implementation().lower() == "cpython"
)


call_stack_inspection_limit = 5


def _should_use_real_time() -> bool:
    if not call_stack_inspection_limit:
        return False

    if not ignore_lists[-1]:
        return False

    try:
        frame = inspect.currentframe().f_back.f_back  # type: ignore
    except AttributeError:
        return False

    for _ in range(call_stack_inspection_limit):
        module_name = frame.f_globals.get('__name__')
        if module_name and module_name.startswith(ignore_lists[-1]):
            return True

        frame = frame.f_back
        if frame is None:
            break

    return False


def get_current_time() -> datetime.datetime:
    return freeze_factories[-1]()


def fake_time() -> float:
    if _should_use_real_time():
        return real_time()
    current_time = get_current_time()
    return real_timegm(current_time.timetuple()) + current_time.microsecond / 1000000.0

if _TIME_NS_PRESENT:
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

def fake_strftime(
    format: str,
    t: Optional[Union[_TimeTuple, time.struct_time]] = None
) -> str:
    if t is None:
        if not _should_use_real_time():
            t = fake_localtime()

    if t is None:
        return real_strftime(format)
    else:
        return real_strftime(format, t)


def fake_timegm(tuple: Union[Tuple[int, ...], time.struct_time]) -> int:
    if _should_use_real_time():
        return real_timegm(tuple)
    else:
        return real_timegm(get_current_time().timetuple())


if real_clock is not None:
    def fake_clock() -> float:
        # Cast since mypy doesn't know this is still available
        _real_clock = cast(Callable[[], float], real_clock)
        if _should_use_real_time():
            return _real_clock()

        if len(freeze_factories) == 1:
            return 0.0 if not tick_flags[-1] else _real_clock()

        first_frozen_time = freeze_factories[0]()
        last_frozen_time = get_current_time()

        timedelta = (last_frozen_time - first_frozen_time)
        total_seconds = timedelta.total_seconds()

        if tick_flags[-1]:
            total_seconds += _real_clock()

        return total_seconds


class FakeDateMeta(type):
    @classmethod
    def __instancecheck__(self, obj: Type[Any]) -> bool:
        return isinstance(obj, real_date)

    @classmethod
    def __subclasscheck__(cls, subclass: Type[Any]) -> bool:
        return issubclass(subclass, real_date)


def datetime_to_fakedatetime(datetime: datetime.datetime) -> 'FakeDatetime':
    return FakeDatetime(datetime.year,
                        datetime.month,
                        datetime.day,
                        datetime.hour,
                        datetime.minute,
                        datetime.second,
                        datetime.microsecond,
                        datetime.tzinfo)


def date_to_fakedate(date: datetime.date) -> 'FakeDate':
    return FakeDate(date.year,
                    date.month,
                    date.day)

class FakeDate(real_date, metaclass=FakeDateMeta):
    def __new__(cls, *args: Any, **kwargs: Any) -> 'FakeDate':
        return real_date.__new__(cls, *args, **kwargs)  # type: ignore

    def __add__(self, other: datetime.timedelta) -> Union[datetime.date, 'FakeDate']:
        result = real_date.__add__(self, other)
        if result is NotImplemented:
            return result
        return date_to_fakedate(result)
    
    @overload
    def __sub__(self, other: datetime.timedelta) -> Union[datetime.date, 'FakeDate']: ...
    @overload
    def __sub__(self, other: datetime.date) -> datetime.timedelta: ...
    def __sub__(self, other: Union[datetime.timedelta, datetime.date]) -> Union[datetime.timedelta, datetime.date, 'FakeDate']:
        result = real_date.__sub__(self, other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_date):
            return date_to_fakedate(result)
        else:
            return result

    @classmethod
    def today(cls) -> 'FakeDate':
        result = cls._date_to_freeze() + cls._tz_offset()
        return date_to_fakedate(result)

    @staticmethod
    def _date_to_freeze() -> datetime.datetime:
        return get_current_time()

    @classmethod
    def _tz_offset(cls) -> datetime.timedelta:
        return tz_offsets[-1]

FakeDate.min = date_to_fakedate(real_date.min)
FakeDate.max = date_to_fakedate(real_date.max)


class FakeDatetimeMeta(FakeDateMeta):
    @classmethod
    def __instancecheck__(self, obj: Type[Any]) -> bool:
        return isinstance(obj, real_datetime)

    @classmethod
    def __subclasscheck__(cls, subclass: Type[Any]) -> bool:
        return issubclass(subclass, real_datetime)


class FakeDatetime(real_datetime, FakeDate, metaclass=FakeDatetimeMeta):
    def __new__(cls, *args: Any, **kwargs: Any) -> 'FakeDatetime':
        return real_datetime.__new__(cls, *args, **kwargs)  # type: ignore

    def __add__(self, other: datetime.timedelta) -> Union['FakeDatetime', datetime.datetime]:
        result = real_datetime.__add__(self, other)
        if result is NotImplemented:
            return result
        return datetime_to_fakedatetime(result)
    
    @overload  # type: ignore
    def __sub__(self, other: datetime.datetime) -> datetime.timedelta: ...
    @overload
    def __sub__(self, other: datetime.timedelta) -> Union[datetime.datetime, 'FakeDatetime']: ...
    def __sub__(
        self,
        other: Union[datetime.datetime, datetime.timedelta]
    ) -> Union[datetime.timedelta, datetime.datetime, 'FakeDatetime']:
        result = real_datetime.__sub__(self, other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_datetime):
            return datetime_to_fakedatetime(result)
        else:
            return result

    def astimezone(self, tz: Optional[datetime.tzinfo] = None) -> 'FakeDatetime':
        if tz is None:
            tz = tzlocal()
        return datetime_to_fakedatetime(real_datetime.astimezone(self, tz))

    @classmethod
    def now(cls, tz: Optional[datetime.tzinfo] = None) -> 'FakeDatetime':
        now = cls._time_to_freeze() or real_datetime.now()  # type: datetime.datetime
        if tz:
            result = tz.fromutc(now.replace(tzinfo=tz)) + cls._tz_offset()
        else:
            result = now + cls._tz_offset()
        return datetime_to_fakedatetime(result)

    def date(self) -> FakeDate:
        return date_to_fakedate(self)

    @property
    def nanosecond(self) -> int:
        return int(getattr(real_datetime, 'nanosecond', 0))

    @classmethod
    def today(cls) -> 'FakeDatetime':
        return cls.now(tz=None)

    @classmethod
    def utcnow(cls) -> 'FakeDatetime':
        result = cls._time_to_freeze() or real_datetime.utcnow()
        return datetime_to_fakedatetime(result)

    @staticmethod
    def _time_to_freeze() -> Optional[datetime.datetime]:
        if freeze_factories:
            return get_current_time()
        return None

    @classmethod
    def _tz_offset(cls) -> datetime.timedelta:
        return tz_offsets[-1]


FakeDatetime.min = datetime_to_fakedatetime(real_datetime.min)
FakeDatetime.max = datetime_to_fakedatetime(real_datetime.max)


def convert_to_timezone_naive(time_to_freeze: datetime.datetime) -> datetime.datetime:
    """
    Converts a potentially timezone-aware datetime to be a naive UTC datetime
    """
    utcoffset = time_to_freeze.utcoffset()
    if utcoffset is not None:
        time_to_freeze -= utcoffset
        time_to_freeze = time_to_freeze.replace(tzinfo=None)
    return time_to_freeze


def pickle_fake_date(datetime_: FakeDate) -> Tuple[Type[FakeDate], Tuple[int, int, int]]:
    # A pickle function for FakeDate
    return FakeDate, (
        datetime_.year,
        datetime_.month,
        datetime_.day,
    )


def pickle_fake_datetime(datetime_: FakeDatetime) -> Tuple[Type[FakeDatetime], Tuple[int, int, int, int, int, int, int, Optional[datetime.tzinfo]]]:
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


def _parse_time_to_freeze(time_to_freeze_str: Optional[_FreezeTimeInputInternalType]) -> datetime.datetime:
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


def _parse_tz_offset(tz_offset: Union[datetime.timedelta, int]) -> datetime.timedelta:
    if isinstance(tz_offset, datetime.timedelta):
        return tz_offset
    else:
        return datetime.timedelta(hours=tz_offset)


class TickingDateTimeFactory(object):
    # time_to_freeze: datetime.datetime
    # start: datetime.datetime

    def __init__(self, time_to_freeze: datetime.datetime, start: datetime.datetime) -> None:
        self.time_to_freeze = time_to_freeze
        self.start = start

    def __call__(self) -> datetime.datetime:
        return self.time_to_freeze + (real_datetime.now() - self.start)


class FrozenDateTimeFactory(object):
    # time_to_freeze: datetime.datetime

    def __init__(self, time_to_freeze: datetime.datetime) -> None:
        self.time_to_freeze = time_to_freeze

    def __call__(self) -> datetime.datetime:
        return self.time_to_freeze

    def tick(self, delta: datetime.timedelta = datetime.timedelta(seconds=1)) -> None:
        if isinstance(delta, numbers.Real):
            # noinspection PyTypeChecker
            self.time_to_freeze += datetime.timedelta(seconds=delta)
        else:
            self.time_to_freeze += delta

    def move_to(self, target_datetime: _FreezeTimeInputInternalType) -> None:
        """Moves frozen date to the given ``target_datetime``"""
        target_datetime = _parse_time_to_freeze(target_datetime)
        delta = target_datetime - self.time_to_freeze
        self.tick(delta=delta)


class StepTickTimeFactory(object):
    # time_to_freeze: datetime.datetime
    # step_width: int

    def __init__(self, time_to_freeze: datetime.datetime, step_width: int) -> None:
        self.time_to_freeze = time_to_freeze
        self.step_width = step_width

    def __call__(self) -> datetime.datetime:
        return_time = self.time_to_freeze
        self.tick()
        return return_time

    def tick(self, delta: Optional[datetime.timedelta] = None) -> None:
        if not delta:
            delta = datetime.timedelta(seconds=self.step_width)
        self.time_to_freeze += delta

    def update_step_width(self, step_width: int) -> None:
        self.step_width = step_width

    def move_to(self, target_datetime: _FreezeTimeInputInternalType) -> None:
        """Moves frozen date to the given ``target_datetime``"""
        target_datetime = _parse_time_to_freeze(target_datetime)
        delta = target_datetime - self.time_to_freeze
        self.tick(delta=delta)

class _freeze_time(object):
    # time_to_freeze: datetime.datetime
    # tz_offset: datetime.timedelta
    # ignore: Tuple[str, ...]
    # tick: bool
    # auto_tick_seconds: int
    # undo_changes: List[Tuple[types.ModuleType, str, Any]]
    # modules_at_start: Set[str]
    # as_arg: bool
    # fake_names: Optional[Tuple[str, ...]]
    # reals: Optional[Mapping[int, object]]

    def __init__(
        self,
        time_to_freeze_str: Optional[_FreezeTimeInputInternalType],
        tz_offset: Union[int, datetime.timedelta],
        ignore: Sequence[str],
        tick: bool,
        as_arg: bool,
        auto_tick_seconds: int
    ) -> None:
        self.time_to_freeze = _parse_time_to_freeze(time_to_freeze_str)
        self.tz_offset = _parse_tz_offset(tz_offset)
        self.ignore = tuple(ignore)
        self.tick = tick
        self.auto_tick_seconds = auto_tick_seconds
        self.undo_changes = []  # type: List[Tuple[types.ModuleType, str, Any]]
        self.modules_at_start = set()  # type: Set[str]
        self.as_arg = as_arg

    def __call__(self, func: _CallableOrTypeT) -> _CallableOrTypeT:
        if inspect.isclass(func):
            return cast(_CallableOrTypeT, self.decorate_class(cast(Any, func)))
        elif iscoroutinefunction(func):
            return self.decorate_coroutine(func)
        return self.decorate_callable(func)

    def decorate_class(self, klass: _TypeT) -> _TypeT:
        if issubclass(klass, unittest.TestCase):
            # If it's a TestCase, we assume you want to freeze the time for the
            # tests, from setUpClass to tearDownClass

            # Use getattr as in Python 2.6 they are optional
            orig_setUpClass = klass.setUpClass
            orig_tearDownClass = klass.tearDownClass

            # noinspection PyDecorator
            @classmethod  # type: ignore
            def setUpClass(cls: Type[unittest.TestCase]) -> None:
                self.start()
                if orig_setUpClass is not None:
                    orig_setUpClass()

            # noinspection PyDecorator
            @classmethod  # type: ignore
            def tearDownClass(cls: Type[unittest.TestCase]) -> None:
                if orig_tearDownClass is not None:
                    orig_tearDownClass()
                self.stop()

            klass.setUpClass = setUpClass
            klass.tearDownClass = tearDownClass

            return klass

        else:
            seen = set()  # type: Set[str]

            if hasattr(klass, 'mro'):
                klasses = klass.mro()  # type: List[Type]
            else:
                klasses = cast(List[Type], [klass]) + list(klass.__bases__)
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
            return klass

    def __enter__(self) -> _FactoryType:
        return self.start()

    def __exit__(self, *args: Any) -> None:
        self.stop()

    def start(self) -> _FactoryType:
        if self.auto_tick_seconds:
            freeze_factory = StepTickTimeFactory(self.time_to_freeze, self.auto_tick_seconds)  # type: _FactoryType
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
        calendar.timegm = fake_timegm

        # ignored for mypy since we cannot assign to types
        datetime.datetime = FakeDatetime  # type: ignore
        datetime.date = FakeDate  # type: ignore

        time.time = fake_time
        time.localtime = fake_localtime
        time.gmtime = fake_gmtime
        time.strftime = fake_strftime
        if uuid_generate_time_attr:
            setattr(uuid, uuid_generate_time_attr, None)
        uuid._UuidCreate = None  # type: ignore
        uuid._last_timestamp = None  # type: ignore

        copyreg.dispatch_table[real_datetime] = pickle_fake_datetime
        copyreg.dispatch_table[real_date] = pickle_fake_date

        # Change any place where the module had already been imported
        to_patch = [
            ('real_date', real_date, FakeDate),
            ('real_datetime', real_datetime, FakeDatetime),
            ('real_gmtime', real_gmtime, fake_gmtime),
            ('real_localtime', real_localtime, fake_localtime),
            ('real_strftime', real_strftime, fake_strftime),
            ('real_time', real_time, fake_time),
            ('real_timegm', real_timegm, fake_timegm),
        ]

        if _TIME_NS_PRESENT:
            setattr(time, 'time_ns', fake_time_ns)
            to_patch.append(('real_time_ns', real_time_ns, fake_time_ns))

        if real_clock is not None:
            # time.clock is deprecated and was removed in Python 3.8
            time.clock = fake_clock
            to_patch.append(('real_clock', real_clock, fake_clock))

        self.fake_names = tuple(getattr(fake, '__name__') for real_name, real, fake in to_patch)
        self.reals = dict((id(fake), real) for real_name, real, fake in to_patch)
        fakes = dict((id(real), fake) for real_name, real, fake in to_patch)
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
            calendar.timegm = real_timegm
            # ignored for mypy since we cannot assign to types
            datetime.datetime = real_datetime  # type: ignore
            datetime.date = real_date  # type: ignore
            copyreg.dispatch_table.pop(real_datetime)
            copyreg.dispatch_table.pop(real_date)
            for module, module_attribute, original_value in self.undo_changes:
                setattr(module, module_attribute, original_value)
            self.undo_changes = []

            # Restore modules loaded after start()
            modules_to_restore = set(sys.modules.keys()) - self.modules_at_start
            self.modules_at_start = set()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                for mod_name in modules_to_restore:
                    to_restore = sys.modules.get(mod_name) 
                    if mod_name is None or to_restore is None:
                        continue
                    elif mod_name.startswith(self.ignore) or mod_name.endswith('.six.moves'):
                        continue
                    elif (not hasattr(to_restore, "__name__") or to_restore.__name__ in ('datetime', 'time')):
                        continue
                    for module_attribute in dir(to_restore):

                        if self.fake_names and module_attribute in self.fake_names:
                            continue
                        try:
                            attribute_value = getattr(to_restore, module_attribute)
                        except (ImportError, AttributeError, TypeError):
                            # For certain libraries, this can result in ImportError(_winreg) or AttributeError (celery)
                            continue

                        real = self.reals.get(id(attribute_value)) if self.reals else None
                        if real:
                            setattr(to_restore, module_attribute, real)

            time.time = real_time
            time.gmtime = real_gmtime
            time.localtime = real_localtime
            time.strftime = real_strftime
            if real_clock:
                time.clock = real_clock

            if uuid_generate_time_attr:
                setattr(uuid, uuid_generate_time_attr, real_uuid_generate_time)
            uuid._UuidCreate = real_uuid_create  # type: ignore
            uuid._last_timestamp = None  # type: ignore

    def decorate_coroutine(self, coroutine: _CallableT) -> _CallableT:
        return wrap_coroutine(self, coroutine)

    def decorate_callable(self, func: _CallableT) -> _CallableT:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self as time_factory:
                if self.as_arg:
                    result = func(time_factory, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)

        # update_wrapper already sets __wrapped__ in Python 3.2+, this is only
        # needed for Python 2.x support
        # wrapper.__wrapped__ = func

        return cast(_CallableT, wrapper)


def freeze_time(
    time_to_freeze: Optional[Union[str, datetime.date, datetime.timedelta, Callable, types.GeneratorType, _MayaDT]] = None,
    tz_offset: Union[int, datetime.timedelta] = 0,
    ignore: Optional[List[str]] = None,
    tick: bool = False,
    as_arg: bool = False,
    auto_tick_seconds: int = 0,
) -> _freeze_time:
    acceptable_times = (type(None), str, datetime.date, datetime.timedelta,
             types.FunctionType, types.GeneratorType)  # type: Tuple[Type,...]

    if _MayaDT is not None:
        acceptable_times += _MayaDT,

    if not isinstance(time_to_freeze, acceptable_times):
        raise TypeError(('freeze_time() expected None, a string, date instance, datetime '
                         'instance, MayaDT, timedelta instance, function or a generator, but got '
                         'type {0}.').format(type(time_to_freeze)))
    if tick and not _is_cpython:
        raise SystemError('Calling freeze_time with tick=True is only compatible with CPython')

    if isinstance(time_to_freeze, types.FunctionType):
        return freeze_time(time_to_freeze(), tz_offset, ignore, tick, as_arg, auto_tick_seconds)

    if isinstance(time_to_freeze, types.GeneratorType):
        return freeze_time(next(time_to_freeze), tz_offset, ignore, tick, as_arg, auto_tick_seconds)

    if _MayaDT is not None and isinstance(time_to_freeze, _MayaDT):
        return freeze_time(time_to_freeze.datetime(), tz_offset, ignore,
                           tick, as_arg, auto_tick_seconds)

    if ignore is None:
        ignore = []
    ignore = ignore[:]
    ignore.append('nose.plugins')
    ignore.append('six.moves')
    ignore.append('django.utils.six.moves')
    ignore.append('google.gax')
    ignore.append('threading')
    ignore.append('Queue')
    ignore.append('selenium')
    ignore.append('_pytest.terminal.')
    ignore.append('_pytest.runner.')

    return _freeze_time(
        cast(Optional[_FreezeTimeInputInternalType], time_to_freeze),
        tz_offset,
        ignore,
        tick,
        as_arg,
        auto_tick_seconds,
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
