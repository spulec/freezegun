import datetime
import functools
import hashlib
import inspect
import sys
import time
import uuid
import calendar
import unittest
import platform
import warnings
import types
import numbers

from dateutil import parser
from dateutil.tz import tzlocal

real_time = time.time
real_localtime = time.localtime
real_gmtime = time.gmtime
real_strftime = time.strftime
real_date = datetime.date
real_datetime = datetime.datetime
real_date_objects = [real_time, real_localtime, real_gmtime, real_strftime, real_date, real_datetime]
_real_time_object_ids = set(id(obj) for obj in real_date_objects)


try:
    real_uuid_generate_time = uuid._uuid_generate_time
except ImportError:
    real_uuid_generate_time = None

try:
    real_uuid_create = uuid._UuidCreate
except ImportError:
    real_uuid_create = None

try:
    import copy_reg as copyreg
except ImportError:
    import copyreg


# keep a cache of module attributes otherwise freezegun will need to analyze too many modules all the time
# start with `None` as the sentinel value.
# if `{}` (empty dict) was the sentinel value, there's a chance that `setup_modules_cache()` will be called many times
_GLOBAL_MODULES_CACHE = None


def _get_global_modules_cache():
    global _GLOBAL_MODULES_CACHE
    # the first call to this function sets up the global module cache. it's expected to be slower than consecutive calls
    if _GLOBAL_MODULES_CACHE is None:
        _GLOBAL_MODULES_CACHE = {}
        _setup_modules_cache()
    return _GLOBAL_MODULES_CACHE


def _get_module_attributes(module):
    result = []
    try:
        module_attributes = dir(module)
    except TypeError:
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


def _setup_modules_cache():
    for mod_name, module in list(sys.modules.items()):
        # ignore modules from freezegun
        if mod_name == __name__ or not mod_name or not module or not hasattr(module, "__name__"):
            continue
        _setup_module_cache(module)


def _setup_module_cache(module):
    global _GLOBAL_MODULES_CACHE
    date_attrs = []
    all_module_attributes = _get_module_attributes(module)
    for attribute_name, attribute_value in all_module_attributes:
        if id(attribute_value) in _real_time_object_ids:
            date_attrs.append((attribute_name, attribute_value))
    _GLOBAL_MODULES_CACHE[module.__name__] = (_get_module_attributes_hash(module), date_attrs)


def _get_module_attributes_hash(module):
    return '{0}-{1}'.format(id(module), hashlib.md5(','.join(dir(module)).encode('utf-8')).hexdigest())


def _get_cached_module_attributes(mod_name, module):
    global_modules_cache = _get_global_modules_cache()
    module_hash, cached_attrs = global_modules_cache.get(mod_name, ('0', []))
    if _get_module_attributes_hash(module) == module_hash:
        return cached_attrs
    else:
        _setup_module_cache(module)
        return _get_module_attributes(module)


# Stolen from six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("NewBase", bases, {})

_is_cpython = (
    hasattr(platform, 'python_implementation') and
    platform.python_implementation().lower() == "cpython"
)


class FakeTime(object):

    def __init__(self, time_to_freeze, previous_time_function):
        self.time_to_freeze = time_to_freeze
        self.previous_time_function = previous_time_function

    def __call__(self):
        current_time = self.time_to_freeze()
        return calendar.timegm(current_time.timetuple()) + current_time.microsecond / 1000000.0


class FakeLocalTime(object):
    def __init__(self, time_to_freeze, previous_localtime_function=None):
        self.time_to_freeze = time_to_freeze
        self.previous_localtime_function = previous_localtime_function

    def __call__(self, t=None):
        if t is not None:
            return real_localtime(t)
        shifted_time = self.time_to_freeze() - datetime.timedelta(seconds=time.timezone)
        return shifted_time.timetuple()


class FakeGMTTime(object):
    def __init__(self, time_to_freeze, previous_gmtime_function):
        self.time_to_freeze = time_to_freeze
        self.previous_gmtime_function = previous_gmtime_function

    def __call__(self, t=None):
        if t is not None:
            return real_gmtime(t)
        return self.time_to_freeze().timetuple()


class FakeStrfTime(object):
    def __init__(self, time_to_freeze, previous_strftime_function):
        self.time_to_freeze = time_to_freeze
        self.previous_strftime_function = previous_strftime_function

    def __call__(self, format, time_to_format=None):
        if time_to_format is None:
            time_to_format = FakeLocalTime(self.time_to_freeze)()
        return real_strftime(format, time_to_format)


class FakeDateMeta(type):
    @classmethod
    def __instancecheck__(self, obj):
        return isinstance(obj, real_date)


def datetime_to_fakedatetime(datetime):
    return FakeDatetime(datetime.year,
                        datetime.month,
                        datetime.day,
                        datetime.hour,
                        datetime.minute,
                        datetime.second,
                        datetime.microsecond,
                        datetime.tzinfo)


def date_to_fakedate(date):
    return FakeDate(date.year,
                    date.month,
                    date.day)


class FakeDate(with_metaclass(FakeDateMeta, real_date)):
    dates_to_freeze = []
    tz_offsets = []

    def __new__(cls, *args, **kwargs):
        return real_date.__new__(cls, *args, **kwargs)

    def __add__(self, other):
        result = real_date.__add__(self, other)
        if result is NotImplemented:
            return result
        return date_to_fakedate(result)

    def __sub__(self, other):
        result = real_date.__sub__(self, other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_date):
            return date_to_fakedate(result)
        else:
            return result

    @classmethod
    def today(cls):
        result = cls._date_to_freeze() + datetime.timedelta(hours=cls._tz_offset())
        return date_to_fakedate(result)

    @classmethod
    def _date_to_freeze(cls):
        return cls.dates_to_freeze[-1]()

    @classmethod
    def _tz_offset(cls):
        return cls.tz_offsets[-1]

FakeDate.min = date_to_fakedate(real_date.min)
FakeDate.max = date_to_fakedate(real_date.max)


class FakeDatetimeMeta(FakeDateMeta):
    @classmethod
    def __instancecheck__(self, obj):
        return isinstance(obj, real_datetime)


class FakeDatetime(with_metaclass(FakeDatetimeMeta, real_datetime, FakeDate)):
    times_to_freeze = []
    tz_offsets = []

    def __new__(cls, *args, **kwargs):
        return real_datetime.__new__(cls, *args, **kwargs)

    def __add__(self, other):
        result = real_datetime.__add__(self, other)
        if result is NotImplemented:
            return result
        return datetime_to_fakedatetime(result)

    def __sub__(self, other):
        result = real_datetime.__sub__(self, other)
        if result is NotImplemented:
            return result
        if isinstance(result, real_datetime):
            return datetime_to_fakedatetime(result)
        else:
            return result

    def astimezone(self, tz=None):
        if tz is None:
            tz = tzlocal()
        return datetime_to_fakedatetime(real_datetime.astimezone(self, tz))

    @classmethod
    def now(cls, tz=None):
        now = cls._time_to_freeze() or real_datetime.now()
        if tz:
            result = tz.fromutc(now.replace(tzinfo=tz)) + datetime.timedelta(hours=cls._tz_offset())
        else:
            result = now + datetime.timedelta(hours=cls._tz_offset())
        return datetime_to_fakedatetime(result)

    def date(self):
        return date_to_fakedate(self)

    @classmethod
    def today(cls):
        return cls.now(tz=None)

    @classmethod
    def utcnow(cls):
        result = cls._time_to_freeze() or real_datetime.utcnow()
        return datetime_to_fakedatetime(result)

    @classmethod
    def _time_to_freeze(cls):
        if cls.times_to_freeze:
            return cls.times_to_freeze[-1]()

    @classmethod
    def _tz_offset(cls):
        return cls.tz_offsets[-1]

FakeDatetime.min = datetime_to_fakedatetime(real_datetime.min)
FakeDatetime.max = datetime_to_fakedatetime(real_datetime.max)


def convert_to_timezone_naive(time_to_freeze):
    """
    Converts a potentially timezone-aware datetime to be a naive UTC datetime
    """
    if time_to_freeze.tzinfo:
        time_to_freeze -= time_to_freeze.utcoffset()
        time_to_freeze = time_to_freeze.replace(tzinfo=None)
    return time_to_freeze


def pickle_fake_date(datetime_):
    # A pickle function for FakeDate
    return FakeDate, (
        datetime_.year,
        datetime_.month,
        datetime_.day,
    )


def pickle_fake_datetime(datetime_):
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


def _parse_time_to_freeze(time_to_freeze_str):
    """Parses all the possible inputs for freeze_time
    :returns: a naive ``datetime.datetime`` object
    """
    if time_to_freeze_str is None:
        time_to_freeze_str = datetime.datetime.utcnow()

    if isinstance(time_to_freeze_str, datetime.datetime):
        time_to_freeze = time_to_freeze_str
    elif isinstance(time_to_freeze_str, datetime.date):
        time_to_freeze = datetime.datetime.combine(time_to_freeze_str, datetime.time())
    else:
        time_to_freeze = parser.parse(time_to_freeze_str)

    return convert_to_timezone_naive(time_to_freeze)


class TickingDateTimeFactory(object):

    def __init__(self, time_to_freeze, start):
        self.time_to_freeze = time_to_freeze
        self.start = start

    def __call__(self):
        return self.time_to_freeze + (real_datetime.now() - self.start)


class FrozenDateTimeFactory(object):

    def __init__(self, time_to_freeze):
        self.time_to_freeze = time_to_freeze

    def __call__(self):
        return self.time_to_freeze

    def tick(self, delta=datetime.timedelta(seconds=1)):
        if isinstance(delta, numbers.Real):
            self.time_to_freeze += datetime.timedelta(seconds=delta)
        else:
            self.time_to_freeze += delta

    def move_to(self, target_datetime):
        """Moves frozen date to the given ``target_datetime``"""
        target_datetime = _parse_time_to_freeze(target_datetime)
        delta = target_datetime - self.time_to_freeze
        self.tick(delta=delta)


class _freeze_time(object):

    def __init__(self, time_to_freeze_str, tz_offset, ignore, tick, as_arg):

        self.time_to_freeze = _parse_time_to_freeze(time_to_freeze_str)
        self.tz_offset = tz_offset
        self.ignore = tuple(ignore)
        self.tick = tick
        self.undo_changes = []
        self.modules_at_start = set()
        self.as_arg = as_arg

    def __call__(self, func):
        if inspect.isclass(func):
            return self.decorate_class(func)
        return self.decorate_callable(func)

    def decorate_class(self, klass):
        if issubclass(klass, unittest.TestCase):
            # If it's a TestCase, we assume you want to freeze the time for the
            # tests, from setUpClass to tearDownClass

            # Use getattr as in Python 2.6 they are optional
            orig_setUpClass = getattr(klass, 'setUpClass', None)
            orig_tearDownClass = getattr(klass, 'tearDownClass', None)

            @classmethod
            def setUpClass(cls):
                self.start()
                if orig_setUpClass is not None:
                    orig_setUpClass()

            @classmethod
            def tearDownClass(cls):
                if orig_tearDownClass is not None:
                    orig_tearDownClass()
                self.stop()

            klass.setUpClass = setUpClass
            klass.tearDownClass = tearDownClass

            return klass

        else:

            seen = set()

            klasses = klass.mro() if hasattr(klass, 'mro') else [klass] + list(klass.__bases__)
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

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        if self.tick:
            time_to_freeze = TickingDateTimeFactory(self.time_to_freeze, real_datetime.now())
        else:
            time_to_freeze = FrozenDateTimeFactory(self.time_to_freeze)

        # Change the modules
        datetime.datetime = FakeDatetime
        datetime.datetime.times_to_freeze.append(time_to_freeze)
        datetime.datetime.tz_offsets.append(self.tz_offset)

        datetime.date = FakeDate
        datetime.date.dates_to_freeze.append(time_to_freeze)
        datetime.date.tz_offsets.append(self.tz_offset)

        fake_time = FakeTime(time_to_freeze, time.time)
        fake_localtime = FakeLocalTime(time_to_freeze, time.localtime)
        fake_gmtime = FakeGMTTime(time_to_freeze, time.gmtime)
        fake_strftime = FakeStrfTime(time_to_freeze, time.strftime)
        time.time = fake_time
        time.localtime = fake_localtime
        time.gmtime = fake_gmtime
        time.strftime = fake_strftime
        uuid._uuid_generate_time = None
        uuid._UuidCreate = None

        copyreg.dispatch_table[real_datetime] = pickle_fake_datetime
        copyreg.dispatch_table[real_date] = pickle_fake_date

        # Change any place where the module had already been imported
        to_patch = [
            ('real_date', real_date, 'FakeDate', FakeDate),
            ('real_datetime', real_datetime, 'FakeDatetime', FakeDatetime),
            ('real_gmtime', real_gmtime, 'FakeGMTTime', fake_gmtime),
            ('real_localtime', real_localtime, 'FakeLocalTime', fake_localtime),
            ('real_strftime', real_strftime, 'FakeStrfTime', fake_strftime),
            ('real_time', real_time, 'FakeTime', fake_time),
        ]
        self.fake_names = tuple(fake_name for real_name, real, fake_name, fake in to_patch)
        self.reals = dict((id(fake), real) for real_name, real, fake_name, fake in to_patch)
        fakes = dict((id(real), fake) for real_name, real, fake_name, fake in to_patch)
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

                module_attrs = _get_cached_module_attributes(mod_name, module)
                for attribute_name, attribute_value in module_attrs:
                    fake = fakes.get(id(attribute_value))
                    if fake:
                        setattr(module, attribute_name, fake)
                        add_change((module, attribute_name, attribute_value))

        return time_to_freeze

    def stop(self):
        datetime.datetime.times_to_freeze.pop()
        datetime.datetime.tz_offsets.pop()
        datetime.date.dates_to_freeze.pop()
        datetime.date.tz_offsets.pop()

        if not datetime.datetime.times_to_freeze:
            datetime.datetime = real_datetime
            datetime.date = real_date
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
                    module = sys.modules.get(mod_name, None)
                    if mod_name is None or module is None:
                        continue
                    elif mod_name.startswith(self.ignore) or mod_name.endswith('.six.moves'):
                        continue
                    elif (not hasattr(module, "__name__") or module.__name__ in ('datetime', 'time')):
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

        time.time = time.time.previous_time_function
        time.gmtime = time.gmtime.previous_gmtime_function
        time.localtime = time.localtime.previous_localtime_function
        time.strftime = time.strftime.previous_strftime_function

        uuid._uuid_generate_time = real_uuid_generate_time
        uuid._UuidCreate = real_uuid_create

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self as time_factory:
                if self.as_arg:
                    result = func(time_factory, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)

        # update_wrapper already sets __wrapped__ in Python 3.2+, this is only
        # needed for Python 2.x support
        wrapper.__wrapped__ = func

        return wrapper


def freeze_time(time_to_freeze=None, tz_offset=0, ignore=None, tick=False, as_arg=False):
    # Python3 doesn't have basestring, but it does have str.
    try:
        string_type = basestring
    except NameError:
        string_type = str

    if not isinstance(time_to_freeze, (type(None), string_type, datetime.date,
        types.FunctionType, types.GeneratorType)):
        raise TypeError(('freeze_time() expected None, a string, date instance, datetime '
                         'instance or function, but got type {0}.').format(type(time_to_freeze)))
    if tick and not _is_cpython:
        raise SystemError('Calling freeze_time with tick=True is only compatible with CPython')

    if isinstance(time_to_freeze, types.FunctionType):
        return freeze_time(time_to_freeze(), tz_offset, ignore, tick)

    if ignore is None:
        ignore = []
    ignore.append('six.moves')
    ignore.append('django.utils.six.moves')
    ignore.append('google.gax')
    ignore.append('threading')
    ignore.append('Queue')
    return _freeze_time(time_to_freeze, tz_offset, ignore, tick, as_arg)


def freeze_times(time_to_freeze=None, tz_offset=0, ignore=None, tick=False):
    if not isinstance(time_to_freeze, types.GeneratorType):
        raise TypeError(('freeze_times() expected a generator, but got type {0}.').format(type(time_to_freeze)))

    return freeze_time(next(time_to_freeze), tz_offset, ignore, tick)


# Setup adapters for sqlite
try:
    import sqlite3
except ImportError:
    # Some systems have trouble with this
    pass
else:
    # These are copied from Python sqlite3.dbapi2
    def adapt_date(val):
        return val.isoformat()

    def adapt_datetime(val):
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
