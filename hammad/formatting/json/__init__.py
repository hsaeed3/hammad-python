"""hammad.formatting.json"""

from typing import TYPE_CHECKING
from ...performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .converters import (
        convert_to_json_schema,
        encode_json,
        decode_json,
    )

__all__ = ("convert_to_json_schema", "encode_json", "decode_json")


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the json module."""
    return list(__all__)
