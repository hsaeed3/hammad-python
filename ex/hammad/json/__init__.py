"""hammad.utils.json"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .converters import (
        convert_to_json_schema,
        encode_json,
        decode_json,
    )

__all__ = ("convert_to_json_schema", "encode_json", "decode_json")


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the json module."""
    return list(__all__)
