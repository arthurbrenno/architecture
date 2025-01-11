"""Creators"""

import importlib
import inspect
from typing import Any, Protocol, TypeGuard, runtime_checkable


@runtime_checkable
class _HasStructFields(Protocol):
    """Protocol for classes (like msgspec.Struct) that define __struct_fields__."""

    __struct_fields__: tuple[str, ...]


def _is_msgspec_struct(cls: type[object]) -> TypeGuard[type[_HasStructFields]]:
    """Runtime check to let static type checkers know cls has __struct_fields__."""
    return hasattr(cls, "__struct_fields__")


class DynamicInstanceCreator[T]:
    """
    A utility class responsible for creating an instance of a class with only the
    parameters that match its constructor or __struct_fields__ (for msgspec.Struct).
    """

    _cls: type[T]

    def __init__(self, cls: type[T]) -> None:
        self._cls = cls

    def create_instance(self, **kwargs: Any) -> T:
        """
        Creates an instance of `cls` by:
            1) Checking if it's a msgspec.Struct (via _is_msgspec_struct),
               and using __struct_fields__ if so.
            2) Otherwise, inspecting the __init__ signature to gather valid parameters.
            3) Filtering out any invalid parameters (unless the class accepts **kwargs).
            4) Calling the constructor exactly once with the filtered arguments.
        """

        if _is_msgspec_struct(self._cls):
            # We know from the type guard that __struct_fields__ is a tuple of str
            valid_parameters: set[str] = set(self._cls.__struct_fields__)
            # msgspec.Struct does not accept **kwargs by default, so filter strictly
            filtered_kwargs: dict[str, Any] = {
                k: v for k, v in kwargs.items() if k in valid_parameters
            }
        else:
            # Use inspect.signature for standard classes / dataclasses
            sig = inspect.signature(self._cls.__init__)
            valid_parameters = set()
            accepts_kwargs = False

            for param in sig.parameters.values():
                # Skip `self` since it's not a constructor argument
                if param.name == "self":
                    continue

                if param.kind == param.VAR_KEYWORD:
                    # If there's a **kwargs in the signature
                    accepts_kwargs = True
                else:
                    valid_parameters.add(param.name)

            if accepts_kwargs:
                # Class can handle arbitrary **kwargs, so no filtering needed
                filtered_kwargs = dict(kwargs)
            else:
                # Filter out anything not in valid_parameters
                filtered_kwargs = {
                    k: v for k, v in kwargs.items() if k in valid_parameters
                }

        # Instantiate the class exactly once with the filtered arguments
        try:
            instance = self._cls(**filtered_kwargs)
        except TypeError as e:
            raise TypeError(
                f"Could not instantiate {self._cls.__name__} with arguments: {filtered_kwargs}\n"
                f"Error: {e}"
            ) from e

        return instance


class ModuleClassLoader:
    """Loader for classes in different modules."""

    class_name: str

    def __init__(self, class_name: str) -> None:
        self.class_name = class_name

    def get_class_from_module(self, module_name: str) -> type[Any]:
        module = importlib.import_module(module_name)
        cls = getattr(module, self.class_name)
        return cls

    def create_instance_from_module(
        self,
        module_name: str,
        **kwargs: Any,
    ) -> Any:
        try:
            cls: type[Any] = self.get_class_from_module(module_name=module_name)

            # Filter kwargs to match the class constructor parameters
            sig = inspect.signature(cls)
            init_params = sig.parameters
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in init_params}

            instance = cls(**filtered_kwargs)
            return instance
        except ImportError as e:
            raise ImportError(f"Could not import module '{module_name}': {e}") from e
        except AttributeError as e:
            raise AttributeError(
                f"Class '{self.class_name}' not found in module '{module_name}': {e}"
            ) from e
        except TypeError as e:
            raise TypeError(
                f"Could not instantiate {self.class_name} from module {module_name}: {e}"
            ) from e
        except Exception as e:
            raise Exception(
                f"An error occurred while creating instance from module: {e}"
            ) from e
