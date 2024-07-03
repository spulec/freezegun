FreezeGun: Deja que tus tests en Python viajen a través del tiempo
==================================================================

.. image:: https://img.shields.io/pypi/v/freezegun.svg
   :target: https://pypi.python.org/pypi/freezegun/
.. image:: https://github.com/spulec/freezegun/workflows/CI/badge.svg
   :target: https://github.com/spulec/freezegun/actions
.. image:: https://coveralls.io/repos/spulec/freezegun/badge.svg?branch=master
   :target: https://coveralls.io/r/spulec/freezegun
.. image:: https://img.shields.io/badge/lang-en-blue.svg
   :target: https://github.com/spulec/freezegun/blob/master/README.rst

FreezeGun es una librería que permite que tus tests de Python viajen a través del tiempo al hacer un mock del módulo `datetime`.

Uso
-----
Una vez el decorador o el `context manager` han sido ejecutados, todas las llamadas a datetime.datetime.now(), datetime.datetime.utcnow(), datetime.date.today(), time.time(), time.localtime(), time.gmtime(), y time.strftime() retornarán la fecha y hora definidas que han sido congeladas. time.monotonic() y time.perf_counter() también tendrán la fecha y hora definidas congeladas; sin embargo no se garantiza su valor absoluto, solo sus cambios en el tiempo.

Decorador
~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time
    import datetime
    import unittest

    # Congela el tiempo para un test que usa pytest:

    @freeze_time("2012-01-14")
    def test():
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    # o para uno que usa unittest TestCase - congela el tiempo para todos los tests
    # y para el código incluido en el set up y en el tear down

    @freeze_time("1955-11-12")
    class MyTests(unittest.TestCase):
        def test_the_class(self):
            assert datetime.datetime.now() == datetime.datetime(1955, 11, 12)

    # o para cualquier otra clase - congela el tiempo en cualquier ejecutable (Pueden existir casos donde no funcione)

    @freeze_time("2012-01-14")
    class Tester(object):
        def test_the_class(self):
            assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    # o como decorador de métodos, también puede pasar el tiempo congelado como kwarg

    class TestUnitTestMethodDecorator(unittest.TestCase):
        @freeze_time('2013-04-09')
        def test_method_decorator_works_on_unittest(self):
            self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())

        @freeze_time('2013-04-09', as_kwarg='frozen_time')
        def test_method_decorator_works_on_unittest(self, frozen_time):
            self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())
            self.assertEqual(datetime.date(2013, 4, 9), frozen_time.time_to_freeze.today())

        @freeze_time('2013-04-09', as_kwarg='hello')
        def test_method_decorator_works_on_unittest(self, **kwargs):
            self.assertEqual(datetime.date(2013, 4, 9), datetime.date.today())
            self.assertEqual(datetime.date(2013, 4, 9), kwargs.get('hello').time_to_freeze.today())

Gestor de contexto (Context manager)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    def test():
        assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
        with freeze_time("2012-01-14"):
            assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
        assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)

Uso puro
~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    freezer = freeze_time("2012-01-14 12:00:01")
    freezer.start()
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14, 12, 0, 1)
    freezer.stop()

Zonas horarias
~~~~~~~~~~~~~~

.. code-block:: python

    from freezegun import freeze_time

    @freeze_time("2012-01-14 03:21:34", tz_offset=-4)
    def test():
        assert datetime.datetime.utcnow() == datetime.datetime(2012, 1, 14, 3, 21, 34)
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 21, 34)

        # datetime.date.today() usa la zona horaria local
        assert datetime.date.today() == datetime.date(2012, 1, 13)

    @freeze_time("2012-01-14 03:21:34", tz_offset=-datetime.timedelta(hours=3, minutes=30))
    def test_timedelta_offset():
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 13, 23, 51, 34)

Entradas estilizadas
~~~~~~~~~~~~~~~~~~~~

FreezeGun usa dateutil tras bambalinas por lo que puedes tener fechas y horas estilizadas.

.. code-block:: python

    @freeze_time("Jan 14th, 2012")
    def test_nice_datetime():
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

Funciones y generadores
~~~~~~~~~~~~~~~~~~~~~~~

FreezeGun puede usarse con funciones y/o generadores.

.. code-block:: python

    def test_lambda():
        with freeze_time(lambda: datetime.datetime(2012, 1, 14)):
            assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)

    def test_generator():
        datetimes = (datetime.datetime(year, 1, 1) for year in range(2010, 2012))

        with freeze_time(datetimes):
            assert datetime.datetime.now() == datetime.datetime(2010, 1, 1)

        with freeze_time(datetimes):
            assert datetime.datetime.now() == datetime.datetime(2011, 1, 1)

        # La próxima llamada a freeze_time(datetimes) generaría la excepción StopIteration.

argumento ``tick``
~~~~~~~~~~~~~~~~~~

FreezeGun tiene un argumento adicional, ``tick``, que reiniciará la fecha y hora en el valor dado, pero el tiempo seguirá corriendo dentro de la ejecución. Es una alternativa a los parámetros por defecto que mantienen el tiempo detenido.

.. code-block:: python

    @freeze_time("Jan 14th, 2020", tick=True)
    def test_nice_datetime():
        assert datetime.datetime.now() > datetime.datetime(2020, 1, 14)

argumento ``auto_tick_seconds``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FreezeGun tiene un argumento adicional, ``auto_tick_seconds``, que autoincrementará el valor del tiempo en el valor dado cada vez que el tiempo es usado, iniciando en el valor inicial del mismo. Es una alternativa a los parámetros por defecto que mantienen el tiempo detenido. Nótese que si se usa ``auto_tick_seconds``, el parámetro ``tick`` será ignorado.

.. code-block:: python

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=15)
    def test_nice_datetime():
        first_time = datetime.datetime.now()
        auto_incremented_time = datetime.datetime.now()
        assert first_time + datetime.timedelta(seconds=15) == auto_incremented_time


Incrementos manuales
~~~~~~~~~~~~~~~~~~~~

FreezeGun también permite que el tiempo avance manualmente.

.. code-block:: python

    def test_manual_tick():
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

.. code-block:: python

    def test_monotonic_manual_tick():
        initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                            hour=15, minute=6, second=3)
        with freeze_time(initial_datetime) as frozen_datetime:
            monotonic_t0 = time.monotonic()
            frozen_datetime.tick(1.0)
            monotonic_t1 = time.monotonic()
            assert monotonic_t1 == monotonic_t0 + 1.0


Moviendo el tiempo a una fecha y hora específica
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FreezeGun permite mover el tiempo a una fecha y hora dada.

.. code-block:: python

    def test_move_to():
        initial_datetime = datetime.datetime(year=1, month=7, day=12,
                                            hour=15, minute=6, second=3)

        other_datetime = datetime.datetime(year=2, month=8, day=13,
                                            hour=14, minute=5, second=0)
        with freeze_time(initial_datetime) as frozen_datetime:
            assert frozen_datetime() == initial_datetime

            frozen_datetime.move_to(other_datetime)
            assert frozen_datetime() == other_datetime

            frozen_datetime.move_to(initial_datetime)
            assert frozen_datetime() == initial_datetime


    @freeze_time("2012-01-14", as_arg=True)
    def test(frozen_time):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
        frozen_time.move_to("2014-02-12")
        assert datetime.datetime.now() == datetime.datetime(2014, 2, 12)

El parámetro ``move_to`` puede ser cualquier fecha válida usada en ``freeze_time`` (string, date, datetime).


Argumentos por defecto
~~~~~~~~~~~~~~~~~~~~~~

Nótese que FreezeGun no modificará los argumentos por defecto. El siguiente código imprimirá la fecha actual.
Revisa `este enlace <http://docs.python-guide.org/en/latest/writing/gotchas/#mutable-default-arguments>`_ para entender por qué.

.. code-block:: python

    from freezegun import freeze_time
    import datetime as dt

    def test(default=dt.date.today()):
        print(default)

    with freeze_time('2000-1-1'):
        test()


Instalación
-----------

Para instalar FreezeGun, simplemente corre:

.. code-block:: bash

    $ pip install freezegun

En sistemas Debian:

.. code-block:: bash

    $ sudo apt-get install python-freezegun


Ignorar paquetes
----------------

Algunas veces es deseable ignorar el comportamiento de FreezeGun en algunos paquetes o librerías.
Es posible hacerlo para un llamado específico:


.. code-block:: python

    from freezegun import freeze_time

    with freeze_time('2020-10-06', ignore=['threading']):
        # ...


Por defecto, FreezeGun ignora los siguientes paquetes:

.. code-block:: python

    [
        'nose.plugins',
        'six.moves',
        'django.utils.six.moves',
        'google.gax',
        'threading',
        'Queue',
        'selenium',
        '_pytest.terminal.',
        '_pytest.runner.',
        'gi',
    ]


Es posible definir una lista de paquetes ignorados propia:

.. code-block:: python

    import freezegun

    freezegun.configure(default_ignore_list=['threading', 'tensorflow'])


Por favor, tener en cuenta que esto sobreescribirá la lista de paquetes ignorados por defecto. Si se quiere extender dicha lista, por favor usar:

.. code-block:: python

    import freezegun

    freezegun.configure(extend_ignore_list=['tensorflow'])
