import datetime
import unittest
from typing import List, Tuple, Type

from freezegun import freeze_time


class TestClassHookBinding(unittest.TestCase):
    def test_class_hooks_bind_to_the_running_class(self) -> None:
        events: List[Tuple[str, Type[unittest.TestCase]]] = []

        @freeze_time("2019-04-14")
        class FrozenTestCase(unittest.TestCase):
            @classmethod
            def setUpClass(cls) -> None:
                events.append(("setup", cls))
                cls.addClassCleanup(events.append, ("cleanup", cls))

            @classmethod
            def tearDownClass(cls) -> None:
                events.append(("teardown", cls))

            def test_frozen_time(self) -> None:
                self.assertEqual(datetime.date.today(), datetime.date(2019, 4, 14))

        class ChildTestCase(FrozenTestCase):
            pass

        self.addCleanup(FrozenTestCase.doClassCleanups)
        for case in (FrozenTestCase, ChildTestCase):
            with self.subTest(case=case.__name__):
                events.clear()
                result = unittest.TestResult()
                unittest.TestSuite([case("test_frozen_time")]).run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                self.assertEqual(events, [
                    ("setup", case),
                    ("teardown", case),
                    ("cleanup", case),
                ])

    def test_staticmethod_hooks_remain_callable(self) -> None:
        events: List[str] = []

        @freeze_time("2019-04-14")
        class FrozenTestCase(unittest.TestCase):
            @staticmethod
            def setUpClass() -> None:
                events.append("setup")

            @staticmethod
            def tearDownClass() -> None:
                events.append("teardown")

            def test_frozen_time(self) -> None:
                self.assertEqual(datetime.date.today(), datetime.date(2019, 4, 14))

        class ChildTestCase(FrozenTestCase):
            pass

        for case in (FrozenTestCase, ChildTestCase):
            with self.subTest(case=case.__name__):
                events.clear()
                result = unittest.TestResult()
                unittest.TestSuite([case("test_frozen_time")]).run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                self.assertEqual(events, ["setup", "teardown"])

    def test_external_bound_hooks_keep_their_receiver(self) -> None:
        events: List[Tuple[str, object]] = []

        class HookOwner:
            def setup(self) -> None:
                events.append(("setup", self))

            def teardown(self) -> None:
                events.append(("teardown", self))

        owner = HookOwner()

        @freeze_time("2019-04-14")
        class FrozenTestCase(unittest.TestCase):
            setUpClass = owner.setup
            tearDownClass = owner.teardown

            def test_frozen_time(self) -> None:
                self.assertEqual(datetime.date.today(), datetime.date(2019, 4, 14))

        class ChildTestCase(FrozenTestCase):
            pass

        for case in (FrozenTestCase, ChildTestCase):
            with self.subTest(case=case.__name__):
                events.clear()
                result = unittest.TestResult()
                unittest.TestSuite([case("test_frozen_time")]).run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                self.assertEqual(events, [("setup", owner), ("teardown", owner)])
