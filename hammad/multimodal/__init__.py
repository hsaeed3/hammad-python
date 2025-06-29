"""hammad.multimodal

Contains types and model like objects for working with various
types of multimodal data."""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .image import Image
    from .audio import Audio


__all__ = (
    "Image",
    "Audio",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
