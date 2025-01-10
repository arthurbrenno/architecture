import asyncio
from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar

from .decorators import pure

T = TypeVar("T")
P = ParamSpec("P")


def file_get_contents(filename: str, cached: bool = False) -> str:
    """Read the contents of a filename and cache the result"""
    return (
        Path(filename).read_text()
        if not cached
        else _file_get_contents_cached(filename)
    )


@pure(cached=True)
def _file_get_contents_cached(filename: str) -> str:
    return Path(filename).read_text()


def run_sync(coro_func, *args, **kwargs):
    """
    Run an async coroutine in a synchronous context.
    """
    try:
        # If this succeeds, it means there's already a running loop in THIS thread
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop -> safe to do `asyncio.run()`
        return asyncio.run(coro_func(*args, **kwargs))
    else:
        # There's a running loop in the current thread -> use that loop
        return loop.run_until_complete(coro_func(*args, **kwargs))


def fire_and_forget(async_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """
    Schedules the async_func to run in the existing event loop if one is running.
    Otherwise, it creates a new event loop and runs the coroutine to completion.

    This function does not wait for the coroutine to finish (fire-and-forget).
    If no loop is detected in the current thread, it will block just long enough
    to run `async_func()` in a newly-created loop (which is closed immediately
    afterward).

    Args:
        async_func: The asynchronous function (coroutine) to run.
        *args: Positional arguments to pass to the coroutine.
        **kwargs: Keyword arguments to pass to the coroutine.
    """
    try:
        loop = asyncio.get_running_loop()
        # We have an event loop running in this thread; schedule the task:
        loop.create_task(async_func(*args, **kwargs))
    except RuntimeError:
        # No running loop in this thread -> create one and run it immediately.
        asyncio.run(async_func(*args, **kwargs))
