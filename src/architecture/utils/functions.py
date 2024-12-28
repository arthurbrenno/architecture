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
    """
    Runs an asynchronous coroutine in a synchronous context with advanced
    handling of cross-thread event loops (for more complex scenarios).

    Handles the following cases:
    1. No event loop is running in any thread: Uses `asyncio.run()`.
    2. An event loop is running in the current thread (main thread): Uses `asyncio.run()`.
    3. An event loop is running in the current thread (non-main thread): Executes on the existing loop.
    4. An event loop is running in a different thread: Raises a RuntimeError.

    Args:
        coro_func: The asynchronous function to execute. Must return a Coroutine.
        *args: Positional arguments to pass to `coro_func`.
        **kwargs: Keyword arguments to pass to `coro_func`.

    Returns:
        The result returned by the coroutine.

    Raises:
        RuntimeError: If an event loop is detected in a different thread or
                     running in the current non-main thread.
        Exception: Propagates any exception raised by the coroutine.
    """
    try:
        loop = asyncio.get_running_loop()
        if (
            loop is not None
            and loop.is_running()
            and threading.current_thread() is threading.main_thread()
        ):
            return asyncio.run(coro_func(*args, **kwargs))
        elif loop is not None and loop.is_running():
            return loop.run_until_complete(coro_func(*args, **kwargs))
    except RuntimeError:
        # No event loop running in the current thread.
        # Check if a loop is running in *any* thread (more expensive check).
        try:
            asyncio.get_event_loop_policy().get_event_loop()
            raise RuntimeError(
                "An event loop is running in a different thread. "
                "Synchronous calls to async functions from different threads are generally unsafe. "
                "Consider using `asyncio.run_coroutine_threadsafe` if cross-thread "
                "interaction is intentionally needed."
            )
        except RuntimeError:
            # No loop running anywhere, safe to create one.
            return asyncio.run(coro_func(*args, **kwargs))
    except Exception:
        raise  # Re-raise any exception from the coroutine
    else:
        # This case is reached if asyncio.get_running_loop() succeeds
        # but neither the 'if' nor the 'elif' condition is met.
        # This means a loop is running in the current thread, but it's not the main thread.
        raise RuntimeError(
            "Cannot run async function synchronously because an event loop is already running in the current (non-main) thread."
        )
