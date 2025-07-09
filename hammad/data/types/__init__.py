"""hammad.data.types

Contains functional alias, or model-like objects that are meant to be used
by users as bases as well as for type hints. These objects define simple
interfaces for various types of common objects."""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from .text import (
        BaseText,
        Text,
    )
    from .file import File
    from .multimodal import (
        Audio,
        Image,
    )


__all__ = (
    # hammad.data.types.text
    "BaseText",
    "Text",
    # hammad.data.types.file
    "File",
    # hammad.data.types.multimodal
    "Audio",
    "Image",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
