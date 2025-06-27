"""hammad.text"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .text import (
        Text,
        CodeSection,
        SchemaSection,
        SimpleText,
        OutputText,
    )
    from .utils.converters import convert_docstring_to_text, convert_type_to_text
    from .utils.markdown.converters import (
        convert_to_markdown as convert_to_text,
    )


__all__ = (
    "Text",
    "CodeSection",
    "SchemaSection",
    "SimpleText",
    "OutputText",
    "convert_docstring_to_text",
    "convert_type_to_text",
    "convert_to_text",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the text module."""
    return list(__all__)
