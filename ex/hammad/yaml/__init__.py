"""hammad.yaml

Simply extends the `msgspec.yaml` submodule."""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .converters import (
        Yaml,
        encode_yaml,
        decode_yaml,
        read_yaml_file,
    )


__all__ = (
    "Yaml",
    "encode_yaml",
    "decode_yaml",
    "read_yaml_file",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the yaml module."""
    return list(__all__)
