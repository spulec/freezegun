FreezeGun: Let your Python tests travel through time
==================================


.. image:: https://secure.travis-ci.org/spulec/freezegun.png?branch=master

FreezeGun is a library that allows you to travel in time with python by mocking the datetime module.

Installation
------------

To install FreezeGun, simply:

.. code-block:: bash

    $ pip install freezegun


Usage
------------

Simple
~~~~~~

.. code-block:: python
    from freezegun import start_freeze, end_freeze

    start_freeze("2012-01-14")
    assert datetime.datetime.now() == datetime.datetime(2012, 01, 14)
    end_freeze()

Decorator
~~~~~~~~~

.. code-block:: python
    from freezegun import freeze_time

    @freeze_time("2012-01-14")
    def test():
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
