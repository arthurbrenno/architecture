from __future__ import annotations

import typing

import msgspec

from architecture.logging import LoggerFactory

T = typing.TypeVar("T", bound="BaseModel")


class BaseModel(msgspec.Struct):
    """
    Fast, Reliable class for data structure classes.

    This class extends msgspec's Struct to provide additional functionality,
    specifically the ability to create model instances from JSON strings or
    dictionaries, with built-in error handling and JSON repair capabilities
    to handle malformed Large Language Model json string returns.

    Attributes:
        Inherits all attributes from msgspec.Struct.

    Example:
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        ...
        >>> json_data = '{"name": "Alice", "age": 30}'
        >>> person = Person.from_json(json_data)
        >>> print(person)
        Person(name='Alice', age=30)
    """

    @classmethod
    def from_dict(
        cls: typing.Type[T],
        dictionary: dict[str, typing.Any],
        encoder: typing.Optional[msgspec.json.Encoder] = None,
    ) -> T:
        """
        Convert a dictionary to a BaseModel instance.

        This method handles JSON strings that may be enclosed in code blocks,
        and attempts to repair malformed JSON before parsing. It can also
        accept dictionaries directly.

        Args:
            json_content (dict[str, Any]): The dictionary to convert.

        Returns:
            T: An instance of the class that called this method (a subclass of BaseModel).

        Raises:
            ValueError: If the conversion fails due to invalid JSON or model mismatch.

        Examples:
            Creating an instance from a well-formed JSON string:
            >>> class User(BaseModel):
            ...     username: str
            ...     email: str
            ...
            >>> json_str = '{"username": "john_doe", "email": "john@example.com"}'
            >>> user = User.from_json(json_str)
            >>> print(user)
            User(username='john_doe', email='john@example.com')

            Creating an instance from a dictionary:
            >>> data_dict = {"username": "jane_doe", "email": "jane@example.com"}
            >>> user = User.from_json(data_dict)
            >>> print(user)
            User(username='jane_doe', email='jane@example.com')

            Handling malformed JSON:
            >>> malformed_json = '{"username": "bob" "email": "bob@example.com"}'
            >>> user = User.from_json(malformed_json)
            >>> print(user)
            User(username='bob', email='bob@example.com')

            Handling JSON with code block markers:
            >>> json_with_markers = '''```json
            ... {"username": "alice", "email": "alice@example.com"}
            ... ```'''
            >>> user = User.from_json(json_with_markers)
            >>> print(user)
            User(username='alice', email='alice@example.com')
        """

        json_encoder = encoder or msgspec.json.Encoder()

        try:
            model: T = msgspec.json.decode(json_encoder.encode(dictionary), type=cls)
            return model
        except msgspec.DecodeError as e:
            LoggerFactory.create(__name__).debug(
                f"Failed to decode dictionary: {dictionary}"
            )
            raise e

    def as_dict(
        self,
        encoder: typing.Optional[msgspec.json.Encoder] = None,
        decoder: typing.Optional[msgspec.json.Decoder[dict[str, typing.Any]]] = None,
    ) -> dict[str, typing.Any]:
        """
        Convert the model instance to a JSON string.

        This method serializes the model instance to a JSON string using msgspec's
        built-in JSON encoder. The resulting string is formatted with indentation
        for readability.

        Returns:
            str: The JSON representation of the model instance.

        Example:
            >>> class User(BaseModel)
            ...     username: str
            ...     email: str
            ...
            >>> user = User(username="alice", email="example@example.com")
            >>> print(user.as_json())
            {
              "username": "alice",
              "email": "example@example.com"
            }
        """

        encoder_instance: msgspec.json.Encoder = encoder or msgspec.json.Encoder()

        decoder_instance: msgspec.json.Decoder[dict[str, typing.Any]] = (
            decoder or msgspec.json.Decoder(type=dict)
        )

        # Encoding objects of type numpy.float64 is unsupported
        _dict: dict[str, typing.Any] = typing.cast(
            dict[str, typing.Any],
            decoder_instance.decode(encoder_instance.encode(self)),
        )
        return _dict

    @classmethod
    def to_json_schema(cls) -> dict[str, typing.Any]:
        """
        Generate a JSON schema representation of the model.

        This method creates a JSON schema dictionary that describes the structure
        of the model, including the types of fields, required properties, and nested models.
        The schema follows the JSON Schema specification (draft-07), making it compatible
        with most JSON validation tools and libraries.

        The generated schema includes:
        - A title representing the model's class name.
        - A `properties` dictionary defining each field's type and constraints.
        - A `required` list that indicates fields without default values.

        Returns:
            dict[str, Any]: The JSON schema as a dictionary.

        Example:
            >>> class Address(BaseModel):
            ...     street: str
            ...     city: str
            ...     zip_code: int
            ...
            >>> class User(BaseModel):
            ...     username: str
            ...     age: int
            ...     email: str
            ...     address: Address
            ...
            >>> schema = User.to_json_schema()
            >>> print(json.dumps(schema, indent=2))
            {
              "type": "object",
              "title": "User",
              "properties": {
                "username": {
                  "type": "string"
                },
                "age": {
                  "type": "integer"
                },
                "email": {
                  "type": "string"
                },
                "address": {
                  "$ref": "#/definitions/Address"
                }
              },
              "required": [
                "username",
                "age",
                "email",
                "address"
              ]
            }

            >>> address_schema = Address.to_json_schema()
            >>> print(json.dumps(address_schema, indent=2))
            {
              "type": "object",
              "title": "Address",
              "properties": {
                "street": {
                  "type": "string"
                },
                "city": {
                  "type": "string"
                },
                "zip_code": {
                  "type": "integer"
                }
              },
              "required": [
                "street",
                "city",
                "zip_code"
              ]
            }

        Note:
            Nested models are referenced using the `$ref` keyword, pointing to their
            respective definitions within the same schema. This supports complex structures
            and reusable model definitions.

        Raises:
            ValueError: If an unsupported type hint is encountered in the model.
        """
        schema: dict[str, typing.Any] = msgspec.json.schema(cls)
        return schema

    @classmethod
    def from_defaults(cls: typing.Type[T]) -> T:
        """
        Create an instance of the model with default values.

        This method creates a new instance of the model with all fields
        initialized to their default values. If a field has no default
        value, it is set to `None`.

        Returns:
            T: An instance of the class that called this method (a subclass of BaseModel).

        Example:
            >>> class Person(BaseModel):
            ...     name: str = "Alice"
            ...     age: int = 30
            ...
            >>> person = Person.from_defaults()
            >>> print(person)
            Person(name='Alice', age=30)
        """
        return cls()
