"""hammad.utils.json"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .converters import (
        convert_to_json_schema,
        encode_json,
        decode_json,
    )

__all__ = ("convert_to_json_schema", "encode_json", "decode_json")


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the json module."""
    return list(__all__)
