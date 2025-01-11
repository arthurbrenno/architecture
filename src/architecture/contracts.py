from __future__ import annotations

from typing import ParamSpec, Protocol, TypeVar, runtime_checkable

# Covariant TypeVars for return types
T_co_sync = TypeVar("T_co_sync", covariant=True)
T_co_async = TypeVar("T_co_async", covariant=True)

# Single ParamSpec for constructor parameters
P = ParamSpec("P")


@runtime_checkable
class Executable(Protocol[T_co_sync]):
    """Protocol for synchronous services within the application."""

    def execute(self) -> T_co_sync:
        """Performs the service's main operations."""
        ...


@runtime_checkable
class AsyncExecutable(Protocol[T_co_async]):
    """Protocol for asynchronous services within the application."""

    async def execute(self) -> T_co_async:
        """Performs the service's main operations asynchronously."""
        ...
