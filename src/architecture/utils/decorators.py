import asyncio
import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    cast,  # Import cast
    overload,
)
import importlib.util
from functools import wraps
from rich.console import Console
from rich.panel import Panel
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



def ensure_module_installed(
    module_name: str, package_name: Optional[str] = None
) -> Callable[..., Any]:
    """
    A decorator that ensures a Python module is installed before executing the function.

    Args:
        module_name: The import name of the module (e.g., 'vertexai.generative_models')
        package_name: Optional pip package name to install (e.g., 'google-cloud-vertexai').
    """

    def ensure():
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            error_message = f"""
[red bold]📦 Import Error: Module Not Found[/red bold]

[yellow]Missing Module:[/yellow] {module_name}
"""
            if package_name:
                error_message += f"""
[green]To fix this, run one of these (according to your package manager):[/green]
[blue]pip install {package_name}[/blue]
[blue]uv add {package_name}[/blue]
[blue]poetry add {package_name}[/blue]
"""
            else:
                error_message += (
                    "\n[dim]Please ensure the module is installed correctly.[/dim]"
                )

            error_message += "\n[dim]For more help, visit our documentation at https://docs.example.com[/dim]"

            console = Console()
            console.print(
                Panel(
                    error_message,
                    title="❌ Error",
                    border_style="red",
                    padding=(1, 2),
                    expand=False,
                )
            )
            raise ImportError(f"Could not find module {module_name}")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check only when the function is called
            ensure()
            return func(*args, **kwargs)
        return wrapper

    return decorator
