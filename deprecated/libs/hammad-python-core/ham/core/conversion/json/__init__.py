"""ham.core.conversion.json"""

from typing import TYPE_CHECKING
from ..._internal import type_checking_importer

if TYPE_CHECKING:
    from .converters import (
        convert_to_json_schema,
        convert_to_json,
        encode_json,
        decode_json,
    )

__all__ = (
    "convert_to_json_schema",
    "convert_to_json",
    "encode_json",
    "decode_json",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the json module."""
    return list(__all__)
