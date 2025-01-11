import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Awaitable, Callable

from .decorators import pure


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


def run_sync[_T](func: Callable[..., Awaitable[_T]], *args, **kwargs) -> _T:
    """
    Runs a callable synchronously. If called from an async context in the main thread,
    it runs the callable in a new event loop in a separate thread. Otherwise, it
    runs the callable directly or using `run_coroutine_threadsafe`.

    Args:
        func: The callable to execute.
        *args: Positional arguments to pass to the callable.
        **kwargs: Keyword arguments to pass to the callable.

    Returns:
        The result of the callable.
    """

    async def _async_wrapper() -> _T:
        return await func(*args, **kwargs)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_async_wrapper())

    if threading.current_thread() is threading.main_thread():
        if not loop.is_running():
            return loop.run_until_complete(_async_wrapper())
        else:

            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(_async_wrapper())
                finally:
                    new_loop.close()

            with ThreadPoolExecutor() as pool:
                future = pool.submit(run_in_new_loop)
                return future.result(30)
    else:
        return asyncio.run_coroutine_threadsafe(_async_wrapper(), loop).result()


def fire_and_forget(async_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """
    Schedules the async_func to run in the existing event loop if one is running.
    Otherwise, it creates a new event loop and runs the coroutine to completion.

    This function does not wait for the coroutine to finish if a loop is already
    running ("fire-and-forget"). If no loop is detected in the current thread,
    it will block just long enough to run `async_func()` in a newly-created loop
    (which is closed immediately afterward).

    Args:
        async_func: The asynchronous function (coroutine) to run.
        *args: Positional arguments to pass to the coroutine.
        **kwargs: Keyword arguments to pass to the coroutine.
    """
    try:
        # Attempt to get a running loop in the current thread.
        loop = asyncio.get_running_loop()

        if loop.is_running():
            # We have a loop, and it's actively running. Schedule the coroutine
            # to run asynchronously (true fire-and-forget).
            loop.create_task(async_func(*args, **kwargs))
        else:
            # We have a loop object in this thread, but it's not actually running.
            # Run the coroutine to completion (blocking briefly).
            loop.run_until_complete(async_func(*args, **kwargs))
    except RuntimeError:
        # No event loop in the current thread -> create one and run the coroutine
        # immediately to completion, then close the loop.
        asyncio.run(async_func(*args, **kwargs))
