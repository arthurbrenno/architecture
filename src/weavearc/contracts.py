from __future__ import annotations

import typing

# Covariant TypeVars for return types
T_co_sync = typing.TypeVar("T_co_sync", covariant=True)
T_co_async = typing.TypeVar("T_co_async", covariant=True)

# Single ParamSpec for constructor parameters
P = typing.ParamSpec("P")


@typing.runtime_checkable
class Executable(typing.Protocol[T_co_sync]):
    """Protocol for synchronous services within the application."""

    def execute(self) -> T_co_sync:
        """Performs the service's main operations."""
        ...


@typing.runtime_checkable
class AsyncExecutable(typing.Protocol[T_co_async]):
    """Protocol for asynchronous services within the application."""

    async def execute(self) -> T_co_async:
        """Performs the service's main operations asynchronously."""
        ...
