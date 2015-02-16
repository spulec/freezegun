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

Installation
------------

To install FreezeGun, simply:

.. code-block:: bash

    $ pip install freezegun

On Debian (Testing and Unstable) systems:

.. code-block:: bash

    $ sudo apt-get install python-freezegun
