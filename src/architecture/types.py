from __future__ import annotations

from typing import Literal

from typing_extensions import override


class NotGiven:
    """
    A sentinel singleton class used to distinguish omitted keyword arguments
    from those passed in with the value None (which may have different behavior).

    For example:

    ```py
    def get(timeout: Union[int, NotGiven, None] = NotGiven()) -> Response: ...


    get(timeout=1)  # 1s timeout
    get(timeout=None)  # No timeout
    get()  # Default timeout behavior, which may not be statically known at the method definition.
    ```
    -> Copied from openai
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NotGiven)

    def __copy__(self) -> NotGiven:
        return self

    def __add__(self, other: object) -> NotGiven:
        return self

    def __deepcopy__(self, memo: dict) -> NotGiven:
        return self

    @override
    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()
