"""hammad.formatting.yaml

Simply extends the `msgspec.yaml` submodule."""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .converters import (
        encode_yaml,
        decode_yaml,
    )


__all__ = (
    "encode_yaml",
    "decode_yaml",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the yaml module."""
    return list(__all__)
