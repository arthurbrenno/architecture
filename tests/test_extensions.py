import unittest
from typing import Callable, Dict, List

from architecture.extensions import Maybe


class TestMaybe(unittest.TestCase):
    def test_initialization(self):
        maybe: Maybe[int] = Maybe(5)
        self.assertEqual(maybe.unwrap(), 5)
        maybe_none: Maybe[int] = Maybe(None)
        self.assertIsNone(maybe_none.unwrap())

    def test_getattr_existing_attribute(self):
        class TestClass:
            def __init__(self):
                self.value = 10

        obj = TestClass()
        maybe_obj: Maybe[TestClass] = Maybe(obj)
        self.assertEqual(maybe_obj.value.unwrap(), 10)

    def test_getattr_nonexistent_attribute(self):
        class TestClass:
            pass

        obj = TestClass()
        maybe_obj: Maybe[TestClass] = Maybe(obj)
        self.assertIsNone(maybe_obj.nonexistent.unwrap())

    def test_call_callable(self):
        def add_one(x: int) -> int:
            return x + 1

        maybe_callable: Maybe[Callable[[int], int]] = Maybe(add_one)
        self.assertEqual(maybe_callable(5).unwrap(), 6)

    def test_call_non_callable(self):
        maybe_non_callable: Maybe[int] = Maybe(10)
        self.assertIsNone(maybe_non_callable(5).unwrap())

    def test_call_none(self):
        maybe_none: Maybe[Callable[[int], int]] = Maybe(None)
        self.assertIsNone(maybe_none(5).unwrap())

    def test_map_existing_value(self):
        maybe: Maybe[int] = Maybe(5)
        self.assertEqual(maybe.map(lambda x: x * 2).unwrap(), 10)

    def test_map_none_value(self):
        maybe_none: Maybe[int] = Maybe(None)
        self.assertIsNone(maybe_none.map(lambda x: x * 2).unwrap())

    def test_map_with_exception(self):
        def risky_function(x: int) -> int:
            return 10 // x

        maybe_zero: Maybe[int] = Maybe(0)
        self.assertIsNone(maybe_zero.map(risky_function).unwrap())

        maybe_five: Maybe[int] = Maybe(5)
        self.assertEqual(maybe_five.map(risky_function).unwrap(), 2)

    def test_bool_true(self):
        maybe_true: Maybe[int] = Maybe(5)
        self.assertTrue(maybe_true)

    def test_bool_false_zero(self):
        maybe_false: Maybe[int] = Maybe(0)
        self.assertFalse(maybe_false)

    def test_bool_false_none(self):
        maybe_none: Maybe[int] = Maybe(None)
        self.assertFalse(maybe_none)

    def test_eq_same_maybe(self):
        maybe1: Maybe[int] = Maybe(5)
        maybe2: Maybe[int] = Maybe(5)
        maybe3: Maybe[int] = Maybe(10)
        self.assertEqual(maybe1, maybe2)
        self.assertNotEqual(maybe1, maybe3)

    def test_eq_with_value(self):
        maybe: Maybe[int] = Maybe(5)
        self.assertEqual(maybe, 5)
        self.assertNotEqual(maybe, 10)

    def test_eq_with_none(self):
        maybe_none: Maybe[int] = Maybe(None)
        self.assertEqual(maybe_none, None)
        self.assertNotEqual(maybe_none, 5)

    def test_hashable(self):
        maybe1: Maybe[int] = Maybe(5)
        maybe2: Maybe[int] = Maybe(5)
        self.assertEqual(hash(maybe1), hash(maybe2))

        maybe_none1: Maybe[None] = Maybe(None)
        maybe_none2: Maybe[None] = Maybe(None)
        self.assertEqual(hash(maybe_none1), hash(maybe_none2))

        maybe3: Maybe[int] = Maybe(10)
        self.assertNotEqual(hash(maybe1), hash(maybe3))

    def test_iterable_wrapped(self):
        maybe_list: Maybe[List[int]] = Maybe([1, 2, 3])
        self.assertEqual(list(maybe_list), [1, 2, 3])

        maybe_string: Maybe[str] = Maybe("abc")
        self.assertEqual(list(maybe_string), ["a", "b", "c"])

        maybe_none: Maybe[List[int]] = Maybe(None)
        self.assertEqual(list(maybe_none), [])

        maybe_non_iterable: Maybe[int] = Maybe(42)
        self.assertEqual(list(maybe_non_iterable), [])

    def test_getitem_existing_key(self):
        maybe_dict: Maybe[Dict[str, int]] = Maybe({"a": 1, "b": 2})
        self.assertEqual(maybe_dict["a"].unwrap(), 1)

    def test_getitem_nonexistent_key(self):
        maybe_dict: Maybe[Dict[str, int]] = Maybe({"a": 1, "b": 2})
        self.assertIsNone(maybe_dict["c"].unwrap())

    def test_getitem_existing_index(self):
        maybe_list: Maybe[List[int]] = Maybe([10, 20, 30])
        self.assertEqual(maybe_list[1].unwrap(), 20)

    def test_getitem_nonexistent_index(self):
        maybe_list: Maybe[List[int]] = Maybe([10, 20, 30])
        self.assertIsNone(maybe_list[5].unwrap())

    def test_getitem_on_none(self):
        maybe_none: Maybe[Dict[str, int]] = Maybe(None)
        self.assertIsNone(maybe_none["a"].unwrap())

    def test_with_default(self):
        maybe_none: Maybe[str] = Maybe(None)
        self.assertEqual(maybe_none.with_default("Default"), "Default")

        maybe_value: Maybe[str] = Maybe("Actual")
        self.assertEqual(maybe_value.with_default("Default"), "Actual")

    def test_and_then(self):
        def to_upper(s: str) -> Maybe[str]:
            return Maybe(s.upper())

        def reverse_string(s: str) -> Maybe[str]:
            return Maybe(s[::-1])

        maybe_str: Maybe[str] = Maybe("hello")
        upper_maybe: Maybe[str] = maybe_str.and_then(to_upper)
        self.assertEqual(upper_maybe.unwrap(), "HELLO")

        chained_optional: Maybe[str] = maybe_str.and_then(to_upper).and_then(
            reverse_string
        )
        self.assertEqual(chained_optional.unwrap(), "OLLEH")

        # Function that returns None
        def to_none(s: str) -> Maybe[str]:
            return Maybe(None)

        chained_none: Maybe[str] = maybe_str.and_then(to_none)
        self.assertIsNone(chained_none.unwrap())

        # Chaining on None
        maybe_initial_none: Maybe[str] = Maybe(None)
        chained_none_initial: Maybe[str] = maybe_initial_none.and_then(to_upper)
        self.assertIsNone(chained_none_initial.unwrap())


if __name__ == "__main__":
    unittest.main()
