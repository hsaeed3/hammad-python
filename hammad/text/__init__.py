"""hammad.text"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .converters import (
        convert_collection_to_text,
        convert_dataclass_to_text,
        convert_dict_to_text,
        convert_docstring_to_text,
        convert_function_to_text,
        convert_pydantic_to_text,
        convert_type_to_text,
        convert_to_text,
    )
    from .markdown import (
        markdown_blockquote,
        markdown_bold,
        markdown_code,
        markdown_code_block,
        markdown_heading,
        markdown_horizontal_rule,
        markdown_italic,
        markdown_link,
        markdown_list_item,
        markdown_table,
        markdown_table_row,
    )
    from .text import (
        BaseText,
        Text,
        OutputText,
        OutputFormat,
        HeadingStyle,
        CodeSection,
        SimpleText,
        SchemaSection,
        UserResponse,
    )


__all__ = (
    # hammad.text.converters
    "convert_collection_to_text",
    "convert_dataclass_to_text",
    "convert_dict_to_text",
    "convert_docstring_to_text",
    "convert_function_to_text",
    "convert_pydantic_to_text",
    "convert_type_to_text",
    "convert_to_text",
    # hammad.text.markdown
    "markdown_blockquote",
    "markdown_bold",
    "markdown_code",
    "markdown_code_block",
    "markdown_heading",
    "markdown_horizontal_rule",
    "markdown_italic",
    "markdown_link",
    "markdown_list_item",
    "markdown_table",
    "markdown_table_row",
    # hammad.text.text
    "BaseText",
    "Text",
    "OutputText",
    "OutputFormat",
    "HeadingStyle",
    "CodeSection",
    "SimpleText",
    "SchemaSection",
    "UserResponse",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
