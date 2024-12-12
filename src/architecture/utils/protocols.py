from typing import Callable, Type, TypeVar

T = TypeVar("T")


def implements(_proto, /) -> Callable[[Type[T]], Type[T]]:
    """
    A decorator to indicate that a class implements a given Protocol.
    This decorator has no runtime impact and serves purely as documentation.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        return cls

    return decorator
