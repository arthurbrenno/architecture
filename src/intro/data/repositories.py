"""Base interfaces for all repositories in the application.

Defines abstract base classes for synchronous and asynchronous repositories, facilitating
data access and manipulation across various storage mechanisms. These base classes ensure
a consistent interface for CRUD operations, supporting a clean architecture and
separation of concerns within the application.
"""

import abc
from typing import (
    Any,
    Generic,
    Optional,
    Protocol,
    Sequence,
    runtime_checkable,
    TypeVar,
)

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class CreateResult:
    """Result of a create operation, including the ID of the created entity."""

    uid: Optional[str]

    def __init__(self, uid: Optional[str] = None) -> None:
        """
        Initialize a CreateResult instance.

        Args:
            uid (Optional[str]): The unique identifier of the created entity. Defaults to None.
        """
        self.uid = uid


class ReadResult(Generic[T_co]):
    """Result of a read operation, including the retrieved entity."""

    entity: T_co

    def __init__(self, entity: T_co) -> None:
        """
        Initialize a ReadResult instance.

        Args:
            entity (Optional[T]): The entity retrieved by the operation. Defaults to None.
        """
        self.entity = entity


class ReadAllResult(Generic[T_co]):
    """Result of a read all operation, including a list of all entities."""

    entities: Sequence[T_co]

    def __init__(self, entities: list[T_co]) -> None:
        """
        Initialize a ReadAllResult instance.

        Args:
            entities (Optional[List[T]]): A list of all entities retrieved. Defaults to an empty list.
        """
        self.entities = entities


class UpdateResult:
    """Result of an update operation, including the number of affected records."""

    def __init__(self, affected_records: int) -> None:
        """
        Initialize an UpdateResult instance.

        Args:
            affected_records (int): The number of affected records. Defaults to 0.
        """
        self.affected_records = affected_records


class DeleteResult:
    """Result of a delete operation, including the number of affected records."""

    def __init__(self, affected_records: int) -> None:
        """
        Initialize a DeleteResult instance.

        Args:
            affected_records (int): The number of affected records. Defaults to 0.
        """
        self.affected_records = affected_records


@runtime_checkable
class AsyncRepository(Protocol[T]):
    @abc.abstractmethod
    async def create(
        self, entity: T, *, filters: Optional[dict[str, Any]] = None
    ) -> CreateResult: ...

    @abc.abstractmethod
    async def read(
        self, q: str, *, filters: Optional[dict[str, Any]] = None
    ) -> ReadResult[T]: ...

    @abc.abstractmethod
    async def read_all(
        self, *, filters: Optional[dict[str, Any]] = None
    ) -> ReadAllResult[T]: ...

    @abc.abstractmethod
    async def update(
        self, q: str, entity: T, *, filters: Optional[dict[str, Any]] = None
    ) -> UpdateResult: ...

    @abc.abstractmethod
    async def delete(
        self, q: str, *, filters: Optional[dict[str, Any]] = None
    ) -> DeleteResult: ...


@runtime_checkable
class Repository(Protocol[T]):
    @abc.abstractmethod
    def create(
        self, entity: T, *, filters: Optional[dict[str, Any]] = None
    ) -> CreateResult: ...

    @abc.abstractmethod
    def read(
        self, q: str, *, filters: Optional[dict[str, Any]] = None
    ) -> ReadResult[T]: ...

    @abc.abstractmethod
    def read_all(
        self, *, filters: Optional[dict[str, Any]] = None
    ) -> ReadAllResult[T]: ...

    @abc.abstractmethod
    def update(
        self, q: str, entity: T, *, filters: Optional[dict[str, Any]] = None
    ) -> UpdateResult: ...

    @abc.abstractmethod
    def delete(
        self, q: str, *, filters: Optional[dict[str, Any]] = None
    ) -> DeleteResult: ...
