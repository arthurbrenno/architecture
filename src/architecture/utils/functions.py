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


def run_sync(
    coro_func: Callable[P, Coroutine[Any, Any, T]], *args: P.args, **kwargs: P.kwargs
) -> T:
    try:
        # Attempt to get a running loop in *this* thread
        loop = asyncio.get_running_loop()
        # If we get here, a loop is running in this thread
        return loop.run_until_complete(coro_func(*args, **kwargs))
    except RuntimeError:
        # Means no loop is running in this thread
        return asyncio.run(coro_func(*args, **kwargs))
