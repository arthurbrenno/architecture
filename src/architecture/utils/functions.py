import asyncio
import threading
from pathlib import Path
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

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
