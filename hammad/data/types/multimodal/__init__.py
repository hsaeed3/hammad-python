"""hammad.types.multimodal

Contains types and model like objects for working with various
types of multimodal data."""

from typing import TYPE_CHECKING
from ...._internal import create_getattr_importer

if TYPE_CHECKING:
    from .image import Image
    from .audio import Audio


__all__ = (
    "Image",
    "Audio",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
