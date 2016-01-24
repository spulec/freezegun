FreezeGun: Let your Python tests travel through time
====================================================


.. image:: https://secure.travis-ci.org/spulec/freezegun.png?branch=master
   :target: https://travis-ci.org/spulec/freezegun
.. image:: https://coveralls.io/repos/spulec/freezegun/badge.png?branch=master
   :target: https://coveralls.io/r/spulec/freezegun

FreezeGun is a library that allows your python tests to travel through time by mocking the datetime module.

Usage
-----

Once the decorator or context manager have been invoked, all calls to datetime.datetime.now(), datetime.datetime.utcnow(), datetime.date.today(), time.time(), time.localtime(), time.gmtime(), and time.strftime() will return the time that has been frozen.

Decorator
~~~~~~~~~

.. code-block:: python

      from freezegun import freeze_time
      import datetime
      import unittest


      @freeze_time("2012-01-14")
      def test():
          assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)

      # Or a unittest TestCase - freezes for every test, from the start of setUpClass to the end of tearDownClass

      @freeze_time("1955-11-12")
      class MyTests(unittest.TestCase):
          def test_the_class(self):
              assert datetime.datetime.now() == datetime.datetime(1955, 11, 12)

      # Or any other class - freezes around each callable (may not work in every case)

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
        assert datetime.date.today() == datetime.date(2012, 01, 13)

Nice inputs
~~~~~~~~~~~

FreezeGun uses dateutil behind the scenes so you can have nice-looking datetimes

.. code-block:: python

    @freeze_time("Jan 14th, 2012")
    def test_nice_datetime():
        assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)

`tick` argument
~~~~~~~~~~~

FreezeGun has an additional `tick` argument which will restart time at the given
value, but then time will keep ticking. This is alternative to the default
parameters which will keep time stopped.

.. code-block:: python

    @freeze_time("Jan 14th, 2020", tick=True)
    def test_nice_datetime():
        assert datetime.datetime.now() > datetime.datetime(2020, 01, 14)

Manual ticks
~~~~~~~~~~~~

Freezegun allows for the time to be manually forwarded as well

.. code-block:: python

    def test_manual_increment():
        initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                            hour=15, minute=6, second=3)
        with freeze_time(initial_datetime) as frozen_datetime:
            assert frozen_datetime() == initial_datetime

            frozen_datetime.tick()
            initial_datetime += datetime.timedelta(seconds=1)
            assert frozen_datetime() == initial_datetime

            frozen_datetime.tick(delta=datetime.timedelta(seconds=10))
            initial_datetime += datetime.timedelta(seconds=10)
            assert frozen_datetime() == initial_datetime


Installation
------------

To install FreezeGun, simply:

.. code-block:: bash

    $ pip install freezegun

On Debian (Testing and Unstable) systems:

.. code-block:: bash

    $ sudo apt-get install python-freezegun
