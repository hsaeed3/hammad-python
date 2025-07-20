"""ham.core.conversion.yaml

Simply extends the `msgspec.yaml` submodule."""

from typing import TYPE_CHECKING
from ..._internal import type_checking_importer

if TYPE_CHECKING:
    from .converters import (
        encode_yaml,
        decode_yaml,
    )


__all__ = (
    "encode_yaml",
    "decode_yaml",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the yaml module."""
    return list(__all__)
