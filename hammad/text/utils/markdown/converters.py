"""hammad.text.utils.markdown.converters"""

import json
import logging
import dataclasses
from dataclasses import is_dataclass, fields as dataclass_fields
from docstring_parser import parse
from typing import (
    Any,
    Optional,
    Dict,
    List,
    Set,
    Callable,
    Union,
)

from ....typing import (
    is_pydantic_basemodel,
    is_pydantic_basemodel_instance,
    is_msgspec_struct,
)
from ...utils.converters import convert_type_to_text as convert_type_to_string
from .formatting import (
    bold,
    italic,
    code,
    code_block,
    heading,
    list_item,
    table_row,
    horizontal_rule,
)


logger = logging.getLogger(__name__)


class MarkdownError(Exception):
    """Exception raised for errors in the markdown converters."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def _escape_markdown(text: str) -> str:
    """Escape special Markdown characters."""
    # Only escape the most problematic characters
    chars_to_escape = ["*", "_", "`", "[", "]", "(", ")", "#", "+", "-", "!"]
    for char in chars_to_escape:
        text = text.replace(char, f"\\{char}")
    return text


def convert_dataclass_to_markdown(
    obj: Any,
    name: Optional[str],
    description: Optional[str],
    table_format: bool,
    show_types: bool,
    show_defaults: bool,
    show_values: bool,
    indent_level: int,
) -> str:
    """Convert a dataclass to Markdown format."""
    is_class = isinstance(obj, type)
    obj_name = name or (obj.__name__ if is_class else obj.__class__.__name__)

    parts = []
    parts.append(heading(obj_name, min(indent_level + 1, 6)))

    if description:
        parts.append(f"\n{description}\n")

    fields_data = []
    for field in dataclass_fields(obj if is_class else obj.__class__):
        field_info = {
            "name": field.name,
            "type": convert_type_to_string(field.type) if show_types else None,
            "default": field.default
            if show_defaults and field.default is not dataclasses.MISSING
            else None,
            "value": getattr(obj, field.name) if show_values and not is_class else None,
        }
        fields_data.append(field_info)

    if table_format and fields_data:
        # Create table headers
        headers = ["Field"]
        if show_types:
            headers.append("Type")
        if show_defaults:
            headers.append("Default")
        if show_values and not is_class:
            headers.append("Value")

        parts.append("\n" + table_row(headers, is_header=True))

        # Add rows
        for field_info in fields_data:
            row = [code(field_info["name"])]
            if show_types:
                row.append(field_info["type"] or "")
            if show_defaults:
                row.append(
                    str(field_info["default"])
                    if field_info["default"] is not None
                    else ""
                )
            if show_values and not is_class:
                row.append(
                    str(field_info["value"]) if field_info["value"] is not None else ""
                )
            parts.append(table_row(row))
    else:
        # List format
        for field_info in fields_data:
            field_desc = code(field_info["name"])
            if field_info["type"]:
                field_desc += f" ({field_info['type']})"
            if field_info["default"] is not None:
                field_desc += f" - default: {field_info['default']}"
            if field_info["value"] is not None:
                field_desc += f" = {field_info['value']}"
            parts.append(list_item(field_desc, indent_level))

    return "\n".join(parts)


def convert_pydantic_to_markdown(
    obj: Any,
    name: Optional[str],
    description: Optional[str],
    table_format: bool,
    show_types: bool,
    show_defaults: bool,
    show_values: bool,
    show_required: bool,
    indent_level: int,
) -> str:
    """Convert a Pydantic model to Markdown format."""
    is_class = isinstance(obj, type)
    is_instance = is_pydantic_basemodel_instance(obj)

    obj_name = name or (obj.__name__ if is_class else obj.__class__.__name__)

    parts = []
    parts.append(heading(obj_name, min(indent_level + 1, 6)))

    if description:
        parts.append(f"\n{description}\n")

    model_fields = getattr(obj if is_class else obj.__class__, "model_fields", {})
    fields_data = []

    for field_name, field_info in model_fields.items():
        field_data = {
            "name": field_name,
            "type": convert_type_to_string(field_info.annotation)
            if show_types
            else None,
            "required": getattr(field_info, "is_required", lambda: True)()
            if show_required
            else None,
            "default": getattr(field_info, "default", None) if show_defaults else None,
            "value": getattr(obj, field_name, None)
            if show_values and is_instance
            else None,
            "description": getattr(field_info, "description", None),
        }
        fields_data.append(field_data)

    if table_format and fields_data:
        # Create table
        headers = ["Field"]
        if show_types:
            headers.append("Type")
        if show_required:
            headers.append("Required")
        if show_defaults:
            headers.append("Default")
        if show_values and is_instance:
            headers.append("Value")

        parts.append("\n" + table_row(headers, is_header=True))

        for field_data in fields_data:
            row = [code(field_data["name"])]
            if show_types:
                row.append(field_data["type"] or "")
            if show_required:
                row.append("Yes" if field_data["required"] else "No")
            if show_defaults:
                row.append(
                    str(field_data["default"])
                    if field_data["default"] is not None
                    else ""
                )
            if show_values and is_instance:
                row.append(
                    str(field_data["value"]) if field_data["value"] is not None else ""
                )
            parts.append(table_row(row))
    else:
        # List format
        for field_data in fields_data:
            field_desc = code(field_data["name"])
            if field_data["type"]:
                field_desc += f" ({field_data['type']})"
            if field_data["required"] is not None:
                field_desc += (
                    " " + bold("[Required]")
                    if field_data["required"]
                    else " " + italic("[Optional]")
                )
            if field_data["default"] is not None:
                field_desc += f" - default: {field_data['default']}"
            if field_data["value"] is not None:
                field_desc += f" = {field_data['value']}"

            parts.append(list_item(field_desc, indent_level))

            if field_data["description"]:
                parts.append(list_item(field_data["description"], indent_level + 1))

    return "\n".join(parts)


def convert_function_to_markdown(
    obj: Callable,
    name: Optional[str],
    description: Optional[str],
    show_signature: bool,
    show_docstring: bool,
    indent_level: int,
) -> str:
    """Convert a function to Markdown format."""
    func_name = name or obj.__name__

    parts = []
    parts.append(heading(func_name, min(indent_level + 1, 6)))

    if show_signature:
        import inspect

        try:
            sig = inspect.signature(obj)
            parts.append(f"\n{code(f'{func_name}{sig}')}\n")
        except Exception:
            pass

    if description:
        parts.append(f"\n{description}\n")
    elif show_docstring and obj.__doc__:
        doc_info = parse(obj.__doc__)
        if doc_info.short_description:
            parts.append(f"\n{doc_info.short_description}\n")
        if doc_info.long_description:
            parts.append(f"\n{doc_info.long_description}\n")

    return "\n".join(parts)


def convert_collection_to_markdown(
    obj: Union[List, Set, tuple],
    name: Optional[str],
    description: Optional[str],
    compact: bool,
    show_indices: bool,
    indent_level: int,
    visited: Set[int],
) -> str:
    """Convert a collection to Markdown format."""
    obj_name = name or obj.__class__.__name__

    parts = []
    if not compact:
        parts.append(heading(obj_name, min(indent_level + 1, 6)))
        if description:
            parts.append(f"\n{description}\n")

    if not obj:
        parts.append(italic("(empty)"))
        return "\n".join(parts)

    for i, item in enumerate(obj):
        if show_indices:
            item_text = (
                f"[{i}] {convert_to_markdown(item, compact=True, _visited=visited)}"
            )
        else:
            item_text = convert_to_markdown(item, compact=True, _visited=visited)
        parts.append(list_item(item_text, indent_level))

    return "\n".join(parts)


def convert_dict_to_markdown(
    obj: Dict[Any, Any],
    name: Optional[str],
    description: Optional[str],
    table_format: bool,
    compact: bool,
    indent_level: int,
    visited: Set[int],
) -> str:
    """Convert a dictionary to Markdown format."""
    obj_name = name or "Dictionary"

    parts = []
    if not compact:
        parts.append(heading(obj_name, min(indent_level + 1, 6)))
        if description:
            parts.append(f"\n{description}\n")

    if not obj:
        parts.append(italic("(empty)"))
        return "\n".join(parts)

    if table_format and all(
        isinstance(v, (str, int, float, bool, type(None))) for v in obj.values()
    ):
        # Use table format for simple values
        parts.append("\n" + table_row(["Key", "Value"], is_header=True))
        for key, value in obj.items():
            parts.append(table_row([code(str(key)), str(value)]))
    else:
        # Use list format
        for key, value in obj.items():
            key_str = code(str(key))
            value_str = convert_to_markdown(value, compact=True, _visited=visited)
            parts.append(list_item(f"{key_str}: {value_str}", indent_level))

    return "\n".join(parts)


# -----------------------------------------------------------------------------
# Main Converter Function
# -----------------------------------------------------------------------------


def convert_to_markdown(
    obj: Any,
    *,
    # Formatting options
    name: Optional[str] = None,
    description: Optional[str] = None,
    heading_level: int = 1,
    table_format: bool = False,
    compact: bool = False,
    code_block_language: Optional[str] = None,
    # Display options
    show_types: bool = True,
    show_values: bool = True,
    show_defaults: bool = True,
    show_required: bool = True,
    show_docstring: bool = True,
    show_signature: bool = True,
    show_indices: bool = False,
    # Style options
    escape_special_chars: bool = False,
    add_toc: bool = False,
    add_horizontal_rules: bool = False,
    # Internal
    _visited: Optional[Set[int]] = None,
    _indent_level: int = 0,
) -> str:
    """
    Converts any object into a Markdown formatted string.

    Args:
        obj: The object to convert to Markdown
        name: Optional name/title for the object
        description: Optional description to add
        heading_level: Starting heading level (1-6)
        table_format: Use tables for structured data when possible
        compact: Minimize formatting for inline usage
        code_block_language: If set, wrap entire output in code block
        show_types: Include type information
        show_values: Show current values (for instances)
        show_defaults: Show default values
        show_required: Show required/optional status
        show_docstring: Include docstrings
        show_signature: Show function signatures
        show_indices: Show indices for collections
        escape_special_chars: Escape Markdown special characters
        add_toc: Add table of contents (not implemented)
        add_horizontal_rules: Add separators between sections

    Returns:
        Markdown formatted string representation of the object
    """
    # Handle circular references
    visited = _visited if _visited is not None else set()
    obj_id = id(obj)

    if obj_id in visited:
        return italic("(circular reference)")

    visited_copy = visited.copy()
    visited_copy.add(obj_id)

    # Handle None
    if obj is None:
        return code("None")

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        text = str(obj)
        if escape_special_chars and isinstance(obj, str):
            text = _escape_markdown(text)
        return text if compact else code(text)

    # Handle bytes
    if isinstance(obj, bytes):
        return code(f"b'{obj.hex()}'")

    # Wrap in code block if requested
    if code_block_language:
        try:
            if code_block_language.lower() == "json":
                content = json.dumps(obj, indent=2)
            else:
                content = str(obj)
            return code_block(content, code_block_language)
        except Exception:
            pass

    result = ""

    # Handle dataclasses
    if is_dataclass(obj):
        result = convert_dataclass_to_markdown(
            obj,
            name,
            description,
            table_format,
            show_types,
            show_defaults,
            show_values,
            _indent_level,
        )

    # Handle Pydantic models
    elif is_pydantic_basemodel(obj):
        result = convert_pydantic_to_markdown(
            obj,
            name,
            description,
            table_format,
            show_types,
            show_defaults,
            show_values,
            show_required,
            _indent_level,
        )

    # Handle msgspec structs
    elif is_msgspec_struct(obj):
        # Similar to dataclass handling
        result = convert_dataclass_to_markdown(
            obj,
            name,
            description,
            table_format,
            show_types,
            show_defaults,
            show_values,
            _indent_level,
        )

    # Handle functions
    elif callable(obj) and hasattr(obj, "__name__"):
        result = convert_function_to_markdown(
            obj, name, description, show_signature, show_docstring, _indent_level
        )

    # Handle collections
    elif isinstance(obj, (list, tuple, set)):
        result = convert_collection_to_markdown(
            obj, name, description, compact, show_indices, _indent_level, visited_copy
        )

    # Handle dictionaries
    elif isinstance(obj, dict):
        result = convert_dict_to_markdown(
            obj, name, description, table_format, compact, _indent_level, visited_copy
        )

    # Default handling
    else:
        obj_name = name or obj.__class__.__name__
        parts = []
        if not compact:
            parts.append(heading(obj_name, min(_indent_level + 1, 6)))
            if description:
                parts.append(f"\n{description}\n")
        parts.append(code(str(obj)))
        result = "\n".join(parts)

    # Add horizontal rule if requested
    if add_horizontal_rules and not compact and _indent_level == 0:
        result += f"\n\n{horizontal_rule()}\n"

    return result
