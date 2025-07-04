"""hammad.formatting

Contains resources for working with various data structures and formats
such as JSON, YAML, and text / markdown formatting."""

from typing import TYPE_CHECKING
from ..performance.imports import create_getattr_importer


if TYPE_CHECKING:
    from .json import (
        convert_to_json_schema,
        encode_json,
        decode_json,
    )
    from .yaml import (
        encode_yaml,
        decode_yaml,
    )


__all__ = (
    # hammad.formatting.json
    "convert_to_json_schema",
    "encode_json",
    "decode_json",
    # hammad.formatting.yaml
    "encode_yaml",
    "decode_yaml",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the formatting module."""
    return list(__all__)
