"""Builder module for providing semantic hints and easier to understand code."""

from __future__ import annotations
from typing import Annotated, Any
import msgspec


class DynamicDict(msgspec.Struct):
    """Constructor parameters for a class."""

    params: Annotated[
        dict[str, Any],
        msgspec.Meta(title="Params", description="Parameters of the constructor"),
    ] = msgspec.field()

    @classmethod
    def having(cls, key: str, /, equals_to: Any) -> DynamicDict:
        return DynamicDict(params={key: equals_to})

    def as_well_as(self, key: str, /, equals_to: Any) -> DynamicDict:
        self.params.update({key: equals_to})
        return self

    def also(self, key: str, /, equals_to: Any, last: bool = False) -> DynamicDict:
        self.params.update({key: equals_to})
        return self

    def at_last(self, key: str, /, equals_to: Any) -> dict[str, Any]:
        self.params.update({key: equals_to})
        return self.params
