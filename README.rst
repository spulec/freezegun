FreezeGun: Let your Python tests travel through time
==================================


.. image:: https://secure.travis-ci.org/spulec/freezegun.png?branch=master

FreezeGun is a library that allows your python tests to travel through time by mocking the datetime module.

Usage
------------

Once the decorator or context manager have been invoked, all calls to datetime.datetime.now(), datetime.datetime.utcnow(), and datetime.date.today() will return the time that has been frozen.

Decorator
~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    @freeze_time("2012-01-14")
    def test():
        assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)

    # Or class based

    @freeze_time("2012-01-14")
    class Tester(object):
        def test_the_class(self):
            assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    def test():
        assert datetime.datetime.now() != datetime.datetime(2012, 01, 14)
        with freeze_time("2012-01-14"):
            assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)
        assert datetime.datetime.now() != datetime.datetime(2012, 01, 14)

Raw use
~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    freezer = freeze_time("2012-01-14 12:00:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 01, 14, 12, 00, 01)
    freezer.stop()

Timezones
~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    @freeze_time("2012-01-14 03:21:34", tz_offset=-4)
    def test():
        assert datetime.datetime.utcnow() == datetime.datetime(2012, 01, 14, 03, 21, 34)
        assert datetime.datetime.now() == datetime.datetime(2012, 01, 13, 23, 21, 34)

        # datetime.date.today() uses local time
        assert datetime.date.today() == datetime.datetime(2012, 01, 13)

Nice inputs
~~~~~~~~~~~

FreezeGun uses dateutil behind the scenes so you can have nice-looking datetimes

.. code-block:: python

    @freeze_time("Jan 14th, 2012")
    def test_nice_datetime():
        assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)

Warning
-------

For the time being, if you use datetime as `from datetime import datetime; now = datetime.now()` then freezegun module must be imported before the datetime module is ever imported for this to work.
If you use datetime as `import datetime; now = datetime.datetime.now()`, then you're good to go without worrying about import order.

Installation
------------

To install FreezeGun, simply:

.. code-block:: bash

    $ pip install freezegun

