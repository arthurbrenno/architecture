"""Creators"""

import importlib
import inspect
import re
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class DynamicInstanceCreator(Generic[T]):
    """A utility class responsible for creating an instance of a class with the maximum number of parameters possible.

    This class examines the constructor (`__init__` method) or class-specific attributes (like `__struct_fields__` for `msgspec.Struct` classes) to determine which parameters are accepted. It then filters the provided keyword arguments to include only those parameters and initializes an instance of the class.

    **Examples:**

    Using a regular class:
    ```python
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    point = DynamicInstanceCreator(Point).create_instance(x=5, y=10, z=15)
    print(point.x, point.y)  # Output: 5 10
    ```

    Using a dataclass:
    ```python
    from dataclasses import dataclass

    @dataclass
    class Rectangle:
        width: int
        height: int
        color: str = 'blue'

    rectangle = DynamicInstanceCreator(Rectangle).create_instance(
        width=10, height=20, color='red', border=True
    )
    print(rectangle)  # Output: Rectangle(width=10, height=20, color='red')
    ```

    Using a `msgspec.Struct` class:
    ```python
    import msgspec
    from typing import Optional

    class User(msgspec.Struct):
        name: str
        email: Optional[str] = None

    user = DynamicInstanceCreator(User).create_instance(
        name='alice', email='alice@example.com', age=30
    )
    print(user)  # Output: User(name='alice', email='alice@example.com')
    ```

    **Attributes:**
        None
    """

    _cls: type[T]

    def __init__(self, cls: type[T]) -> None:
        self._cls = cls

    def create_instance(self, **kwargs: Any) -> T:
        """Creates an instance of `cls` with as many parameters from `kwargs` as possible.

        The method attempts to instantiate the class with all provided `kwargs`. If it encounters a
        `TypeError` due to unexpected keyword arguments, it removes the offending arguments and retries.
        This process repeats until the instance is successfully created or no more arguments can be removed.

        **Args:**
            cls: The class to instantiate.
            **kwargs: Keyword arguments to pass to the class constructor.

        **Returns:**
            An instance of `cls` initialized with the maximum number of parameters possible.

        **Raises:**
            TypeError: If the class cannot be instantiated with the filtered parameters.

        **Examples:**

        Using a regular class:
        ```python
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        point = DynamicInstanceCreator(Point).create_instance(x=5, y=10, z=15)
        print(point.x, point.y)  # Output: 5 10
        ```

        Using a dataclass:
        ```python
        from dataclasses import dataclass

        @dataclass
        class Rectangle:
            width: int
            height: int
            color: str = 'blue'

        rectangle = DynamicInstanceCreator(Rectangle).create_instance(
            width=10, height=20, color='red', border=True
        )
        print(rectangle)  # Output: Rectangle(width=10, height=20, color='red')
        ```

        Using a `msgspec.Struct` class:
        ```python
        import msgspec
        from typing import Optional

        class User(msgspec.Struct):
            name: str
            email: Optional[str] = None

        user = DynamicInstanceCreator(User).create_instance(
            name='alice', email='alice@example.com', age=30
        )
        print(user)  # Output: User(name='alice', email='alice@example.com')
        ```

        Using a class that accepts `**kwargs`:
        ```python
        class FlexibleClass:
            def __init__(self, x, **kwargs):
                self.x = x
                self.options = kwargs

        instance = DynamicInstanceCreator(FlexibleClass).create_instance(
            x=10, y=20, z=30
        )
        print(instance.x)          # Output: 10
        print(instance.options)    # Output: {'y': 20, 'z': 30}
        ```

        Passing invalid arguments:
        ```python
        class SimpleClass:
            def __init__(self, a, b):
                self.a = a
                self.b = b

        instance = DynamicInstanceCreator(SimpleClass).create_instance(
            a=1, b=2, c=3, d=4
        )
        print(instance.a)  # Output: 1
        print(instance.b)  # Output: 2
        ```

        **Notes:**
            - The method handles classes that use `**kwargs` by attempting to pass all provided arguments.
            - If unexpected keyword arguments are provided to classes that do not accept them, the method
              removes the offending arguments and retries instantiation.
            - The method limits the number of attempts to prevent infinite loops.

        """
        valid_kwargs = kwargs.copy()
        max_attempts = len(valid_kwargs) + 1  # Prevent infinite loops
        attempts = 0

        while attempts < max_attempts:
            try:
                instance = self._cls(**valid_kwargs)
                return instance
            except TypeError as e:
                message = str(e)
                # Check for unexpected keyword argument
                match = re.search(
                    r"__init__\(\) got an unexpected keyword argument '(?P<arg>\w+)'",
                    message,
                )
                if match:
                    arg_name = match.group("arg")
                    if arg_name in valid_kwargs:
                        del valid_kwargs[arg_name]
                        attempts += 1
                        continue
                    else:
                        raise TypeError(
                            f"Argument '{arg_name}' caused an error but was not in kwargs."
                        ) from e
                # Check for multiple values for argument (e.g., when an argument is specified more than once)
                match = re.search(
                    r"__init__\(\) got multiple values for argument '(?P<arg>\w+)'",
                    message,
                )
                if match:
                    arg_name = match.group("arg")
                    if arg_name in valid_kwargs:
                        del valid_kwargs[arg_name]
                        attempts += 1
                        continue
                    else:
                        raise TypeError(
                            f"Argument '{arg_name}' caused an error but was not in kwargs."
                        ) from e
                # Check for missing required positional arguments
                match = re.search(
                    r"__init__\(\) missing \d+ required positional argument[s]?: (.+)",
                    message,
                )
                if match:
                    missing_args = match.group(1)
                    raise TypeError(
                        f"Cannot instantiate {self._cls.__name__}: missing required arguments {missing_args}"
                    ) from e
                # If the error is not about unexpected keyword arguments, re-raise it
                raise TypeError(f"Cannot instantiate {self._cls.__name__}: {e}") from e

        raise TypeError(
            f"Could not instantiate {self._cls.__name__} with provided arguments after {max_attempts} attempts."
        )


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
            cls: type[Any] = self.get_class_from_module(
                module_name=module_name
            )

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
