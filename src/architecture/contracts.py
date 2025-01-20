from __future__ import annotations

from typing import ParamSpec, Protocol, runtime_checkable


# Single ParamSpec for constructor parameters
P = ParamSpec("P")


@runtime_checkable
class Executable[T_co](Protocol):
    """Protocol for synchronous services within the application."""

    def execute(self) -> T_co:
        """Performs the service's main operations."""
        ...


@runtime_checkable
class AsyncExecutable[T_co](Protocol):
    """Protocol for asynchronous services within the application."""

    async def execute(self) -> T_co:
        """Performs the service's main operations asynchronously."""
        ...
