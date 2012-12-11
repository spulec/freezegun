FreezeGun: Let your Python tests travel through time
==================================


.. image:: https://secure.travis-ci.org/spulec/freezegun.png?branch=master

FreezeGun is a library that allows your python tests to travel through time by mocking the datetime module.

Usage
------------

Simple
~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    freezer = freeze_time("2012-01-14 12:00:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 01, 14, 12, 00, 01)
    freezer.stop()

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


Installation
------------

To install FreezeGun, simply:

.. code-block:: bash

    $ pip install freezegun

