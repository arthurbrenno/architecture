"""
This module contains marker decorators for classes.

These markers serve two purposes:

1. To annotate classes with their intended roles or characteristics, enhancing
    code readability and maintainability.
2. To be used by the `generate_code_metrics` function (in a separate module)
    to count the occurrences of each marker throughout the codebase.
"""

MARKER_COUNTS: dict[str, set[type]] = {}


def _register_marker(marker_name: str, cls: type) -> None:
    """Registers that a marker was applied to a class."""
    if marker_name not in MARKER_COUNTS:
        MARKER_COUNTS[marker_name] = set()
    MARKER_COUNTS[marker_name].add(cls)


def Factory[T](cls: type[T]) -> type[T]:
    """Marks a class as a Factory."""
    _register_marker("Factory", cls)
    return cls


def Singleton[T](cls: type[T]) -> type[T]:
    """Marks a class as a Singleton."""
    _register_marker("Singleton", cls)
    return cls


def Observer[T](cls: type[T]) -> type[T]:
    """Marks a class as an Observer."""
    _register_marker("Observer", cls)
    return cls


def Decorator[T](cls: type[T]) -> type[T]:
    """Marks a class as a Decorator."""
    _register_marker("Decorator", cls)
    return cls


def Adapter[T](cls: type[T]) -> type[T]:
    """Marks a class as an Adapter."""
    _register_marker("Adapter", cls)
    return cls
