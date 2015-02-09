import datetime
import functools
import inspect
import sys
import time

from dateutil import parser

real_time = time.time
real_localtime = time.localtime
real_gmtime = time.gmtime
real_strftime = time.strftime
real_date = datetime.date
real_datetime = datetime.datetime

try:
    import copy_reg as copyreg
except ImportError:
    import copyreg

# Stolen from six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("NewBase", bases, {})


class FakeTime(object):

    def __init__(self, time_to_freeze, previous_time_function):
        self.time_to_freeze = time_to_freeze
        self.previous_time_function = previous_time_function

    def __call__(self):
        shifted_time = self.time_to_freeze - datetime.timedelta(seconds=time.timezone)
        return time.mktime(shifted_time.timetuple()) + shifted_time.microsecond / 1000000.0


class FakeLocalTime(object):
    def __init__(self, time_to_freeze):
        self.time_to_freeze = time_to_freeze

    def __call__(self, t=None):
        if t is not None:
            return real_localtime(t)
        shifted_time = self.time_to_freeze - datetime.timedelta(seconds=time.timezone)
        return shifted_time.timetuple()


class FakeGMTTime(object):
    def __init__(self, time_to_freeze):
        self.time_to_freeze = time_to_freeze

    def __call__(self, t=None):
        if t is not None:
            return real_gmtime(t)
        return self.time_to_freeze.timetuple()


class FakeStrfTime(object):
    def __init__(self, default_fake_time):
        self.default_fake_time = default_fake_time

    def __call__(self, format, time_to_format=None):
        if time_to_format is None:
            time_to_format = FakeLocalTime(self.default_fake_time)()
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
        result = cls._date_to_freeze()
        return date_to_fakedate(result)

    @classmethod
    def _date_to_freeze(cls):
        return cls.dates_to_freeze[-1]

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

    def astimezone(self, tz):
        return datetime_to_fakedatetime(real_datetime.astimezone(self, tz))

    @classmethod
    def now(cls, tz=None):
        if tz:
            result = tz.fromutc(cls._time_to_freeze().replace(tzinfo=tz)) + datetime.timedelta(hours=cls._tz_offset())
        else:
            result = cls._time_to_freeze() + datetime.timedelta(hours=cls._tz_offset())
        return datetime_to_fakedatetime(result)

    @classmethod
    def today(cls):
        return cls.now(tz=None)

    @classmethod
    def utcnow(cls):
        result = cls._time_to_freeze()
        return datetime_to_fakedatetime(result)

    @classmethod
    def _time_to_freeze(cls):
        return cls.times_to_freeze[-1]

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
        time_to_freeze =  time_to_freeze.replace(tzinfo=None)
    return time_to_freeze


def pickle_fake_date(datetime_):
    # A pickle function for FakeDate
    return FakeDate, (datetime_.year,
        datetime_.month,
        datetime_.day,
    )


def pickle_fake_datetime(datetime_):
    # A pickle function for FakeDatetime
    return FakeDatetime, (datetime_.year,
        datetime_.month,
        datetime_.day,
        datetime_.hour,
        datetime_.minute,
        datetime_.second,
        datetime_.microsecond,
        datetime_.tzinfo,
    )


class _freeze_time(object):

    def __init__(self, time_to_freeze_str, tz_offset, ignore):
        time_to_freeze = parser.parse(time_to_freeze_str)
        time_to_freeze = convert_to_timezone_naive(time_to_freeze)

        self.time_to_freeze = time_to_freeze
        self.tz_offset = tz_offset
        self.ignore = ignore
        self.undo_changes = []

    def __call__(self, func):
        if inspect.isclass(func):
            return self.decorate_class(func)
        return self.decorate_callable(func)

    def decorate_class(self, klass):
        for attr in dir(klass):
            if attr.startswith("_"):
                continue

            attr_value = getattr(klass, attr)
            if not hasattr(attr_value, "__call__"):
                continue

            # Check if this is a classmethod. If so, skip patching
            if inspect.ismethod(attr_value) and attr_value.__self__ is klass:
                continue

            try:
                setattr(klass, attr, self(attr_value))
            except TypeError:
                # Sometimes we can't set this for built-in types
                continue
        return klass

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        # Change the modules
        datetime.datetime = FakeDatetime
        datetime.date = FakeDate
        fake_time = FakeTime(self.time_to_freeze, time.time)
        fake_localtime = FakeLocalTime(self.time_to_freeze)
        fake_gmtime = FakeGMTTime(self.time_to_freeze)
        fake_strftime = FakeStrfTime(self.time_to_freeze)
        time.time = fake_time
        time.localtime = fake_localtime
        time.gmtime = fake_gmtime
        time.strftime = fake_strftime

        copyreg.dispatch_table[real_datetime] = pickle_fake_datetime
        copyreg.dispatch_table[real_date] = pickle_fake_date

        # Change any place where the module had already been imported
        for mod_name, module in list(sys.modules.items()):
            if mod_name is None or module is None:
                continue
            if mod_name.startswith(tuple(self.ignore)):
                continue
            if (not hasattr(module, "__name__")
                or module.__name__ in ['datetime', 'time']):
                continue
            for module_attribute in dir(module):
                if module_attribute in ['real_date', 'real_datetime',
                    'real_time', 'real_localtime', 'real_gmtime', 'real_strftime']:
                    continue
                try:
                    attribute_value = getattr(module, module_attribute)
                except (ImportError, AttributeError):
                    # For certain libraries, this can result in ImportError(_winreg) or AttributeError (celery)
                    continue
                try:
                    if attribute_value is real_datetime:
                        setattr(module, module_attribute, FakeDatetime)
                        self.undo_changes.append((module, module_attribute, real_datetime))
                    elif attribute_value is real_date:
                        setattr(module, module_attribute, FakeDate)
                        self.undo_changes.append((module, module_attribute, real_date))
                    elif attribute_value is real_time:
                        setattr(module, module_attribute, fake_time)
                        self.undo_changes.append((module, module_attribute, real_time))
                    elif attribute_value is real_localtime:
                        setattr(module, module_attribute, fake_localtime)
                        self.undo_changes.append((module, module_attribute, real_localtime))
                    elif attribute_value is real_gmtime:
                        setattr(module, module_attribute, fake_gmtime)
                        self.undo_changes.append((module, module_attribute, real_gmtime))
                    elif attribute_value is real_strftime:
                        setattr(module, module_attribute, fake_strftime)
                        self.undo_changes.append((module, module_attribute, real_strftime))
                except:
                    # If it's not possible to compare the value to real_XXX (e.g. hiredis.version)
                    pass

        datetime.datetime.times_to_freeze.append(self.time_to_freeze)
        datetime.datetime.tz_offsets.append(self.tz_offset)

        # Since datetime.datetime has already been mocked, just use that for
        # calculating the date
        datetime.date.dates_to_freeze.append(datetime.datetime.now().date())

    def stop(self):
        datetime.datetime.times_to_freeze.pop()
        datetime.datetime.tz_offsets.pop()
        if not datetime.datetime.times_to_freeze:
            datetime.datetime = real_datetime
            copyreg.dispatch_table.pop(real_datetime)

        datetime.date.dates_to_freeze.pop()
        if not datetime.date.dates_to_freeze:
            datetime.date = real_date
            copyreg.dispatch_table.pop(real_date)

        time.time = time.time.previous_time_function

        for module, module_attribute, original_value in self.undo_changes:
            setattr(module, module_attribute, original_value)

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)

        # update_wrapper already sets __wrapped__ in Python 3.2+, this is only
        # needed for Python 2.x support
        wrapper.__wrapped__ = func

        return wrapper


def freeze_time(time_to_freeze, tz_offset=0, ignore=None):
    if isinstance(time_to_freeze, datetime.date):
        time_to_freeze = time_to_freeze.isoformat()

    # Python3 doesn't have basestring, but it does have str.
    try:
        string_type = basestring
    except NameError:
        string_type = str

    if not isinstance(time_to_freeze, string_type):
        raise TypeError(('freeze_time() expected a string, date instance, or '
                         'datetime instance, but got type {0}.').format(type(time_to_freeze)))
    if ignore is None:
        ignore = []
    ignore.append('six.moves.')
    ignore.append('django.utils.six.moves.')
    return _freeze_time(time_to_freeze, tz_offset, ignore)


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
