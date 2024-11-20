from .decorators import pure
from pathlib import Path


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
