from __future__ import annotations

import typing

import msgspec


class NotGiven(msgspec.Struct, frozen=True):  # type: ignore[call-arg]
    """
    `NotGiven` is a sentinel class used to distinguish between `None`, actual values,
    and values that have not been provided (i.e., absent).

    This class is particularly useful in scenarios where you need to differentiate
    between a parameter explicitly set to `None` and a parameter that was omitted
    or not provided at all.

    Attributes:
        None

    Example:
        ```python
        from typing import Optional

        def update_user(name: Optional[str] = NotGiven()):
            if NotGiven.is_absent(name):
                print("Name not provided.")
            elif name is None:
                print("Name set to None.")
            else:
                print(f"Name updated to {name}.")

        update_user()                  # Output: Name not provided.
        update_user(None)              # Output: Name set to None.
        update_user("Alice")           # Output: Name updated to Alice.
        ```
    """

    @classmethod
    def is_absent(cls, obj: typing.Any) -> bool:
        """
        Determine whether the provided object is an instance of `NotGiven`,
        indicating that the value was not provided.

        Args:
            obj (Any): The object to check.

        Returns:
            bool: `True` if `obj` is an instance of `NotGiven`, otherwise `False`.

        Example:
            ```python
            print(NotGiven.is_absent(NotGiven()))  # Output: True
            print(NotGiven.is_absent(None))         # Output: False
            print(NotGiven.is_absent("value"))      # Output: False
            ```
        """
        return isinstance(obj, NotGiven)
