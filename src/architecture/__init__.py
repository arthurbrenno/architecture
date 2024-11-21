"""
The architecture your project needs.
"""

from msgspec import Meta, field

from .data import (
    AsyncRepository,
    CreateResult,
    DeleteResult,
    BaseModel,
    ReadAllResult,
    ReadResult,
    Repository,
    UpdateResult,
)
from .contracts import AsyncExecutable, Executable
from .utils.builders import DynamicDict
from .utils.markers import NotGiven

__all__: list[str] = [
    "BaseModel",
    "field",
    "Meta",
    "Meta",
    "field",
    "AsyncRepository",
    "Repository",
    "ReadAllResult",
    "ReadResult",
    "CreateResult",
    "UpdateResult",
    "DeleteResult",
    "AsyncExecutable",
    "DynamicDict",
    "Executable",
    "NotGiven",
]
