import asyncio
import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    TypeVar,
    Union,
    overload,
    ParamSpec,
    cast,  # Import cast
)

from aiocache import cached as aiocache_decorator  # type: ignore[import-untyped]

# Define type variables
P = ParamSpec("P")
R = TypeVar("R")


def is_coroutine_function(func: Callable[..., Any]) -> bool:
    return asyncio.iscoroutinefunction(func)


@overload
def pure(
    func: Callable[P, R],
    *,
    cached: bool = ...,
    maxsize: Optional[int] = ...,
    ttl: Optional[int] = ...,
) -> Callable[P, R]: ...


@overload
def pure(
    func: None = ...,
    *,
    cached: bool = ...,
    maxsize: Optional[int] = ...,
    ttl: Optional[int] = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def pure(
    func: Optional[Callable[P, Union[R, Awaitable[R]]]] = None,
    *,
    cached: bool = False,
    maxsize: Optional[int] = None,
    ttl: Optional[int] = None,
) -> Union[
    Callable[P, Union[R, Awaitable[R]]],
    Callable[
        [Callable[P, Union[R, Awaitable[R]]]], Callable[P, Union[R, Awaitable[R]]]
    ],
]:
    """
    Decorator to cache functions, supporting both synchronous and asynchronous functions.

    Args:
        func: The function to decorate. Can be None if used with arguments.
        cached: Whether to apply caching. Defaults to False.
        maxsize: Maximum size of the cache (for synchronous functions).
        ttl: Time-to-live for cache entries (for asynchronous functions).

    Raises:
        ValueError: If both maxsize and ttl are provided, or if cached is False but maxsize/ttl are set.
    """

    def decorator(
        inner_func: Callable[P, Union[R, Awaitable[R]]],
    ) -> Callable[P, Union[R, Awaitable[R]]]:
        # Validation
        if not cached:
            if maxsize is not None or ttl is not None:
                raise ValueError("Cannot set maxsize or ttl when cached is False.")
            return inner_func

        if maxsize is not None and ttl is not None:
            raise ValueError("Cannot set both maxsize and ttl at the same time.")

        if is_coroutine_function(inner_func):
            if maxsize is not None:
                raise ValueError("maxsize cannot be used with asynchronous functions.")
            # Apply aiocache decorator
            cache_kwargs: dict[str, Any] = {}
            if ttl is not None:
                cache_kwargs["ttl"] = ttl
            decorated_func = aiocache_decorator(**cache_kwargs)(inner_func)
            return cast(Callable[P, Union[R, Awaitable[R]]], decorated_func)
        else:
            if ttl is not None:
                raise ValueError("ttl cannot be used with synchronous functions.")
            # Apply functools.lru_cache decorator
            cache_kwargs = {}
            if maxsize is not None:
                cache_kwargs["maxsize"] = maxsize
            else:
                cache_kwargs["maxsize"] = 128  # Default maxsize
            decorated_func = functools.lru_cache(**cache_kwargs)(inner_func)
            return cast(Callable[P, Union[R, Awaitable[R]]], decorated_func)

    if func is None:
        return decorator
    else:
        return decorator(func)
