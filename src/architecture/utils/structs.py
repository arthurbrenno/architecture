from typing import Any, Optional, TypeVar
import msgspec

S = TypeVar("S", bound=msgspec.Struct)


def structify(
    data: dict[str, Any],
    struct: type[S],
    decoder: Optional[msgspec.json.Decoder[S]] = None,
    encoder: Optional[msgspec.json.Encoder] = None,
) -> S:
    """Create a struct from a dictionary"""
    decoder = decoder or msgspec.json.Decoder(type=struct)
    encoder = encoder or msgspec.json.Encoder()
    _struct: S = decoder.decode(encoder.encode(data))
    return _struct


def dictify(
    struct: msgspec.Struct,
    encoder: Optional[msgspec.json.Encoder] = None,
    decoder: Optional[msgspec.json.Decoder[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Create a dictionary from a struct"""
    encoder = encoder or msgspec.json.Encoder()
    decoder = decoder or msgspec.json.Decoder(type=dict)
    return decoder.decode(encoder.encode(struct))
