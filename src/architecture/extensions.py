from __future__ import annotations

import collections.abc  # Required for runtime type checks
from typing import (
    Any,
    Callable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    cast,
    overload,
)

import msgspec
from pydantic_core import core_schema

U = TypeVar("U")
K = TypeVar("K")
V = TypeVar("V")


class Maybe[T = object](msgspec.Struct, frozen=True):
    """
    A class that safely handles optional chaining for Python objects, emulating the `?.` operator
    found in languages like JavaScript. This allows for safe access to attributes and methods
    of objects that may be `None`, preventing `AttributeError` exceptions.

    **Usage Patterns:**

    1. **Type Annotation with Instance Creation:**
       ```python
       user_instance = User("Alice")
       maybe_user: Maybe[User] = Maybe(user_instance)
       ```

    2. **Handling Optional Values:**
       ```python
       maybe_none_user: Maybe[User] = Maybe(None)
       ```

    **Usage Examples:**

    ```python
    >>> # Type annotation with instance creation
    >>> user_instance = User("Alice")
    >>> maybe_user: Maybe[User] = Maybe(user_instance)
    >>> maybe_user.name.unwrap()
    'Alice'

    >>> # Handling None
    >>> maybe_none_user: Maybe[User] = Maybe(None)
    >>> maybe_none_user.name.unwrap()
    None

    >>> # Wrapping a callable
    >>> def greet(user: User) -> str:
    ...     return f"Hello, {user.name}!"
    >>> maybe_greet: Maybe[Callable[[User], str]] = Maybe(greet)
    >>> maybe_greet(user_instance).unwrap()
    'Hello, Alice!'

    >>> # Wrapping a non-callable
    >>> maybe_not_callable: Maybe[int] = Maybe(42)
    >>> maybe_not_callable("Test").unwrap()
    None

    >>> # Using map to transform the wrapped value
    >>> maybe_number: Maybe[int] = Maybe(10)
    >>> maybe_double: Maybe[int] = maybe_number.map(lambda x: x * 2)
    >>> maybe_double.unwrap()
    20

    >>> # Using with_default to provide fallback
    >>> maybe_none: Maybe[str] = Maybe(None)
    >>> maybe_none.with_default("Default Value")
    'Default Value'

    >>> # Using and_then for chaining
    >>> maybe_upper: Maybe[str] = maybe_user.and_then(lambda user: Maybe(user.name.upper()))
    >>> maybe_upper.unwrap()
    'ALICE'

    >>> # Iterating over a wrapped list
    >>> maybe_list: Maybe[list[int]] = Maybe([1, 2, 3])
    >>> list(maybe_list)
    [1, 2, 3]

    >>> # Accessing items with __getitem__
    >>> maybe_dict: Maybe[dict[str, int]] = Maybe({"a": 1, "b": 2})
    >>> maybe_dict["a"].unwrap()
    1

    >>> maybe_dict["c"].unwrap()
    None
    ```
    """

    obj: Optional[T] = None

    def __getattr__(self, attr: str) -> Maybe[object]:
        """
        Safely access an attribute of the wrapped object.

        Args:
            attr (str): The attribute name to access.

        Returns:
            Maybe[Any]: An instance of `Maybe` wrapping the attribute's value or `None`.

        Examples:
            >>> class User:
            ...     def __init__(self, name):
            ...         self.name = name
            >>> user = User("Alice")
            >>> maybe_user: Maybe[User] = Maybe(user)
            >>> maybe_user.name.unwrap()
            'Alice'

            >>> maybe_none: Maybe[User] = Maybe(None)
            >>> maybe_none.name.unwrap()
            None
        """
        if self.obj is None:
            return Maybe[object](None)
        try:
            return Maybe[object](getattr(self.obj, attr))
        except AttributeError:
            return Maybe[object](None)

    def __call__(self, *args: Any, **kwargs: Any) -> Maybe[object]:
        """
        Safely call the wrapped object if it's callable.

        Args:
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            Maybe[Any]: An instance of `Maybe` wrapping the result of the call or `None`.

        Examples:
            >>> def greet(user: User) -> str:
            ...     return f"Hello, {user.name}!"
            >>> maybe_greet: Maybe[Callable[[User], str]] = Maybe(greet)
            >>> maybe_greet(user_instance).unwrap()
            'Hello, Alice!'

            >>> maybe_callable_none: Maybe[Callable[[User], str]] = Maybe(None)
            >>> maybe_callable_none(user_instance).unwrap()
            None

            >>> maybe_not_callable: Maybe[int] = Maybe(42)
            >>> maybe_not_callable("Test").unwrap()
            None
        """

        if self.obj is None or not callable(self.obj):
            return Maybe[object](obj=None)
        try:
            result = self.obj(*args, **kwargs)
            return Maybe[object](obj=result)
        except Exception:
            return Maybe[object](obj=None)

    def map(self, func: Callable[[T], U]) -> Maybe[U]:
        """
        Apply a function to the wrapped object if it's not `None`.

        Args:
            func (Callable[[T], U]): A callable that takes the wrapped object and returns a new value.

        Returns:
            Maybe[U]: An instance of `Maybe` wrapping the function's result or `None`.

        Examples:
            >>> maybe_number: Maybe[int] = Maybe(10)
            >>> maybe_double: Maybe[int] = maybe_number.map(lambda x: x * 2)
            >>> maybe_double.unwrap()
            20

            >>> maybe_none: Maybe[str] = Maybe(None)
            >>> maybe_none.map(lambda x: x.upper()).unwrap()
            None

            >>> def risky_division(x: int) -> float:
            ...     return 10 / x
            >>> maybe_zero: Maybe[int] = Maybe(0)
            >>> maybe_zero.map(risky_division).unwrap()
            None  # Due to ZeroDivisionError

            >>> maybe_five: Maybe[int] = Maybe(5)
            >>> maybe_five.map(risky_division).unwrap()
            2.0
        """
        if self.obj is None:
            return Maybe[U](obj=None)
        try:
            return Maybe[U](obj=func(self.obj))
        except Exception:
            return Maybe[U](obj=None)

    def unwrap(self) -> Optional[T]:
        """
        Retrieve the underlying object.

        Returns:
            Optional[T]: The wrapped object if not `None`; otherwise, `None`.

        Examples:
            >>> maybe = Maybe("Hello")
            >>> maybe.unwrap()
            'Hello'

            >>> maybe_none = Maybe(None)
            >>> maybe_none.unwrap()
            None
        """
        return self.obj

    def __bool__(self) -> bool:
        """
        Allow `Maybe` instances to be used in boolean contexts.

        Returns:
            bool: `True` if the wrapped object is truthy; `False` otherwise.

        Examples:
            >>> maybe_true: Maybe[int] = Maybe(5)
            >>> bool(maybe_true)
            True

            >>> maybe_false: Maybe[int] = Maybe(0)
            >>> bool(maybe_false)
            False

            >>> maybe_none: Maybe[int] = Maybe(None)
            >>> bool(maybe_none)
            False
        """
        return bool(self._obj)

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison between `Maybe` instances or with raw values.

        Args:
            other (object): Another `Maybe` instance or a raw value to compare with.

        Returns:
            bool: `True` if both wrapped objects are equal; `False` otherwise.

        Examples:
            >>> maybe1: Maybe[int] = Maybe(5)
            >>> maybe2: Maybe[int] = Maybe(5)
            >>> maybe3: Maybe[int] = Maybe(10)
            >>> maybe1 == maybe2
            True
            >>> maybe1 == maybe3
            False
            >>> maybe1 == 5
            True
            >>> maybe_none: Maybe[int] = Maybe(None)
            >>> maybe_none == None
            True
        """
        if isinstance(other, Maybe):
            return self._obj == other._obj
        return self._obj == other

    def __ne__(self, other: object) -> bool:
        """
        Non-equality comparison between `Maybe` instances or with raw values.

        Args:
            other (object): Another `Maybe` instance or a raw value to compare with.

        Returns:
            bool: `True` if both wrapped objects are not equal; `False` otherwise.

        Examples:
            >>> maybe1: Maybe[int] = Maybe(5)
            >>> maybe2: Maybe[int] = Maybe(5)
            >>> maybe3: Maybe[int] = Maybe(10)
            >>> maybe1 != maybe2
            False
            >>> maybe1 != maybe3
            True
            >>> maybe1 != 5
            False
            >>> maybe_none: Maybe[int] = Maybe(None)
            >>> maybe_none != None
            False
        """
        return not self.__eq__(other)

    def __iter__(self) -> Iterator[Any]:
        """
        Allow iteration over the wrapped object if it's iterable.

        Yields:
            Any: Items from the wrapped iterable or nothing if the wrapped object is `None`.

        Examples:
            >>> maybe_list: Maybe[list[int]] = Maybe([1, 2, 3])
            >>> list(maybe_list)
            [1, 2, 3]

            >>> maybe_string: Maybe[str] = Maybe("abc")
            >>> list(maybe_string)
            ['a', 'b', 'c']

            >>> maybe_none: Maybe[list[int]] = Maybe(None)
            >>> list(maybe_none)
            []
        """
        if self.obj is not None and isinstance(self.obj, collections.abc.Iterable):
            # We do a runtime ignore on the type of `iter(obj)` because T might not be known to be iterable.
            return iter(self.obj)
        return iter(())

    @overload
    def __getitem__(self: Maybe[Mapping[K, V]], key: K) -> Maybe[V]: ...

    @overload
    def __getitem__(self: Maybe[Sequence[V]], key: int) -> Maybe[V]: ...

    @overload
    def __getitem__(self, key: object) -> Maybe[object]: ...

    def __getitem__(self, key: object) -> Maybe[Any]:
        """
        Safely access an item by key/index if the wrapped object supports indexing.

        Args:
            key (Any): The key/index to access.

        Returns:
            Maybe[Any]: An instance of `Maybe` wrapping the item's value or `None`.

        Examples:
            >>> maybe_dict: Maybe[dict[str, int]] = Maybe({"a": 1, "b": 2})
            >>> maybe_dict["a"].unwrap()
            1

            >>> maybe_dict["c"].unwrap()
            None

            >>> maybe_list: Maybe[list[int]] = Maybe([10, 20, 30])
            >>> maybe_list[1].unwrap()
            20

            >>> maybe_none: Maybe[dict[str, int]] = Maybe(None)
            >>> maybe_none["a"].unwrap()
            None
        """
        if self.obj is None:
            return Maybe(None)

        # 1) If obj is a Mapping, key must be the type of mapping keys (K).
        if isinstance(self.obj, Mapping):
            try:
                return Maybe(self.obj[key])
            except (KeyError, TypeError):
                return Maybe(None)

        # 2) If obj is a Sequence, key must be int or slice.
        elif isinstance(self.obj, Sequence):
            if not isinstance(key, (int, slice)):
                return Maybe(None)
            try:
                return Maybe(self.obj[key])
            except (IndexError, TypeError):
                return Maybe(None)

        # 3) If it just has __getitem__, we can attempt calling it:
        elif hasattr(self.obj, "__getitem__"):
            try:
                return Maybe(cast(Mapping, self.obj)[key])
            except (IndexError, KeyError, TypeError, AttributeError):
                return Maybe(None)

        return Maybe(None)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Define how pydantic should handle the Maybe class during serialization and deserialization.
        """
        # Extract the type argument T from Maybe[T]
        wrapped_type = source_type.__args__[0]

        # Get the schema for the wrapped type T
        wrapped_schema = handler(wrapped_type)

        # Define the validation function (accepts only 'value')
        def validate(value: Any) -> Maybe[T]:
            return cls(value)

        # Define the serialization function (accepts only 'value')
        def serialize(value: "Maybe[T]") -> Any:
            return value.unwrap()

        # Create and return the CoreSchema
        schema = core_schema.no_info_after_validator_function(
            validate,
            wrapped_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=False
            ),
        )
        return schema

    def with_default(self, default: T) -> T:
        """
        Provide a default value if the wrapped object is `None`.

        Args:
            default (T): The default value to return if the wrapped object is `None`.

        Returns:
            T: The wrapped object if not `None`; otherwise, the default value.

        Examples:
            >>> maybe_none: Maybe[str] = Maybe(None)
            >>> maybe_none.with_default("Default Value")
            'Default Value'

            >>> maybe_value: Maybe[str] = Maybe("Actual Value")
            >>> maybe_value.with_default("Default Value")
            'Actual Value'
        """
        return self.obj if self.obj is not None else default

    def and_then(self, func: Callable[[T], Maybe[U]]) -> Maybe[U]:
        """
        Chain operations that return `Maybe` instances.

        Args:
            func (Callable[[T], Maybe[U]]): A callable that takes the wrapped object and returns a `Maybe` instance.

        Returns:
            Maybe[U]: The result of the callable or `Maybe(None)` if the wrapped object is `None`.

        Examples:
            >>> def to_upper(s: str) -> Maybe[str]:
            ...     return Maybe(s.upper())
            >>> maybe_str: Maybe[str] = Maybe("hello")
            >>> upper_optional: Maybe[str] = maybe_str.and_then(to_upper)
            >>> upper_optional.unwrap()
            'HELLO'

            >>> def reverse_string(s: str) -> Maybe[str]:
            ...     return Maybe(s[::-1])
            >>> chained_optional: Maybe[str] = maybe_str.and_then(to_upper).and_then(reverse_string)
            >>> chained_optional.unwrap()
            'OLLEH'

            >>> def to_none(s: str) -> Maybe[str]:
            ...     return Maybe(None)
            >>> chained_none: Maybe[str] = maybe_str.and_then(to_none)
            >>> chained_none.unwrap()
            None

            >>> maybe_initial_none: Maybe[str] = Maybe(None)
            >>> chained_none_initial: Maybe[str] = maybe_initial_none.and_then(to_upper)
            >>> chained_none_initial.unwrap()
            None
        """
        if self.obj is None:
            return Maybe[U](obj=None)
        try:
            return func(self.obj)
        except Exception:
            return Maybe[U](obj=None)
