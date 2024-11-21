from __future__ import annotations

import collections.abc  # Required for runtime type checks
import typing

from pydantic_core import core_schema

T = typing.TypeVar("T")
U = typing.TypeVar("U")
K = typing.TypeVar("K")
V = typing.TypeVar("V")


class Maybe(typing.Generic[T]):
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
    >>> maybe_greet: Maybe[typing.Callable[[User], str]] = Maybe(greet)
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

    def __init__(self, obj: typing.Optional[T]) -> None:
        """
        Initialize the `Maybe` wrapper.

        Args:
            obj (typing.Optional[T]): The object to wrap, which may be `None`.

        Examples:
            >>> maybe = Maybe("Hello")
            >>> maybe.unwrap()
            'Hello'

            >>> maybe_none = Maybe(None)
            >>> maybe_none.unwrap()
            None
        """
        self._obj: typing.Optional[T] = obj

    def __getattr__(self, attr: str) -> Maybe[typing.Any]:
        """
        Safely access an attribute of the wrapped object.

        Args:
            attr (str): The attribute name to access.

        Returns:
            Maybe[typing.Any]: An instance of `Maybe` wrapping the attribute's value or `None`.

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
        if self._obj is None:
            return Maybe(None)
        try:
            attr_value = getattr(self._obj, attr)
            return Maybe(attr_value)
        except AttributeError:
            return Maybe(None)

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> Maybe[typing.Any]:
        """
        Safely call the wrapped object if it's callable.

        Args:
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            Maybe[typing.Any]: An instance of `Maybe` wrapping the result of the call or `None`.

        Examples:
            >>> def greet(user: User) -> str:
            ...     return f"Hello, {user.name}!"
            >>> maybe_greet: Maybe[typing.Callable[[User], str]] = Maybe(greet)
            >>> maybe_greet(user_instance).unwrap()
            'Hello, Alice!'

            >>> maybe_callable_none: Maybe[typing.Callable[[User], str]] = Maybe(None)
            >>> maybe_callable_none(user_instance).unwrap()
            None

            >>> maybe_not_callable: Maybe[int] = Maybe(42)
            >>> maybe_not_callable("Test").unwrap()
            None
        """
        if self._obj is None or not callable(self._obj):
            return Maybe(None)
        try:
            result = self._obj(*args, **kwargs)
            return Maybe(result)
        except Exception:
            return Maybe(None)

    def map(self, func: typing.Callable[[T], U]) -> Maybe[U]:
        """
        Apply a function to the wrapped object if it's not `None`.

        Args:
            func (typing.Callable[[T], U]): A callable that takes the wrapped object and returns a new value.

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
        if self._obj is None:
            return Maybe(None)
        try:
            return Maybe(func(self._obj))
        except Exception:
            return Maybe(None)

    def unwrap(self) -> typing.Optional[T]:
        """
        Retrieve the underlying object.

        Returns:
            typing.Optional[T]: The wrapped object if not `None`; otherwise, `None`.

        Examples:
            >>> maybe = Maybe("Hello")
            >>> maybe.unwrap()
            'Hello'

            >>> maybe_none = Maybe(None)
            >>> maybe_none.unwrap()
            None
        """
        return self._obj

    def __repr__(self) -> str:
        """
        Return the official string representation of the `Maybe`.

        Returns:
            str: A string representation of the `Maybe` instance.

        Examples:
            >>> maybe = Maybe("Hello")
            >>> repr(maybe)
            "Maybe('Hello')"

            >>> maybe_none = Maybe(None)
            >>> repr(maybe_none)
            'Maybe(None)'
        """
        return f"Maybe({self._obj!r})"

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

    def __hash__(self) -> int:
        """
        Make `Maybe` instances hashable if the wrapped object is hashable.

        Returns:
            int: The hash of the wrapped object.

        Raises:
            TypeError: If the wrapped object is unhashable.

        Examples:
            >>> maybe1: Maybe[int] = Maybe(5)
            >>> maybe2: Maybe[int] = Maybe(5)
            >>> hash(maybe1) == hash(maybe2)
            True

            >>> maybe_none1: Maybe[None] = Maybe(None)
            >>> maybe_none2: Maybe[None] = Maybe(None)
            >>> hash(maybe_none1) == hash(maybe_none2)
            True

            >>> maybe_unhashable: Maybe[list[int]] = Maybe([1, 2, 3])
            >>> hash(maybe_unhashable)
            Traceback (most recent call last):
                ...
            TypeError: unhashable type: 'list'
        """
        if self._obj is None:
            return hash(None)
        return hash(self._obj)

    def __iter__(self) -> typing.Iterator[typing.Any]:
        """
        Allow iteration over the wrapped object if it's iterable.

        Yields:
            typing.Any: Items from the wrapped iterable or nothing if the wrapped object is `None`.

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
        if self._obj is not None and isinstance(self._obj, collections.abc.Iterable):
            return iter(self._obj)
        return iter(())  # Return empty iterator if not iterable

    @typing.overload
    def __getitem__(self: Maybe[typing.Mapping[K, V]], key: K) -> Maybe[V]: ...

    @typing.overload
    def __getitem__(self: Maybe[typing.Sequence[V]], key: int) -> Maybe[V]: ...

    @typing.overload
    def __getitem__(self: Maybe[typing.Any], key: typing.Any) -> Maybe[typing.Any]: ...

    def __getitem__(self, key: typing.Any) -> Maybe[typing.Any]:
        """
        Safely access an item by key/index if the wrapped object supports indexing.

        Args:
            key (typing.Any): The key/index to access.

        Returns:
            Maybe[typing.Any]: An instance of `Maybe` wrapping the item's value or `None`.

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
        if self._obj is None:
            return Maybe(None)
        try:
            if isinstance(self._obj, collections.abc.Mapping):
                mapping_obj = typing.cast(
                    collections.abc.Mapping[typing.Any, typing.Any], self._obj
                )
                return Maybe(mapping_obj[key])
            elif isinstance(self._obj, collections.abc.Sequence):
                sequence_obj = typing.cast(
                    collections.abc.Sequence[typing.Any], self._obj
                )
                return Maybe(sequence_obj[key])
            elif hasattr(self._obj, "__getitem__"):
                indexable_obj = typing.cast(typing.Any, self._obj)
                return Maybe(indexable_obj[key])
            return Maybe(None)
        except (IndexError, KeyError, TypeError):
            return Maybe(None)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: typing.Any,
        handler: typing.Callable[[typing.Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Define how pydantic should handle the Maybe class during serialization and deserialization.
        """
        # Extract the type argument T from Maybe[T]
        wrapped_type = source_type.__args__[0]

        # Get the schema for the wrapped type T
        wrapped_schema = handler(wrapped_type)

        # Define the validation function (accepts only 'value')
        def validate(value: typing.Any) -> Maybe[T]:
            return cls(value)

        # Define the serialization function (accepts only 'value')
        def serialize(value: "Maybe[T]") -> typing.Any:
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
        return self._obj if self._obj is not None else default

    def and_then(self, func: typing.Callable[[T], Maybe[U]]) -> Maybe[U]:
        """
        Chain operations that return `Maybe` instances.

        Args:
            func (typing.Callable[[T], Maybe[U]]): A callable that takes the wrapped object and returns a `Maybe` instance.

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
        if self._obj is None:
            return Maybe(None)
        try:
            return func(self._obj)
        except Exception:
            return Maybe(None)
