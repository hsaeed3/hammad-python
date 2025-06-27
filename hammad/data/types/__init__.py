"""hammad.data.types

Contains various explicit data models and definitions for
various file types, data formats, and other data related
concepts."""

from typing import TYPE_CHECKING
from ...based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .files.audio import Audio
    from .files.configuration import Configuration
    from .files.document import Document
    from .files.file import File, FileSource
    from .files.image import Image


__all__ = (
    "Audio",
    "Configuration",
    "Document",
    "File",
    "FileSource",
    "Image",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.types module."""
    return list(__all__)
