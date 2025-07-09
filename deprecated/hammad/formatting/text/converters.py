"""hammad.formatting.text.converters"""

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

from ...typing import (
    inspection,
    is_pydantic_basemodel,
    is_msgspec_struct,
    is_dataclass,
    is_pydantic_basemodel_instance,
)
from .markdown import (
    markdown_bold,
    markdown_italic,
    markdown_code,
    markdown_code_block,
    markdown_heading,
    markdown_list_item,
    markdown_table_row,
    markdown_horizontal_rule,
)

__all__ = [
    "convert_type_to_text",
    "convert_docstring_to_text",
    "convert_dataclass_to_text",
    "convert_pydantic_to_text",
    "convert_function_to_text",
    "convert_collection_to_text",
    "convert_dict_to_text",
    "convert_to_text",
]


class TextFormattingError(Exception):
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


def convert_type_to_text(cls: Any) -> str:
    """Converts a type into a clean & human readable text representation.

    This function uses `typing_inspect` exclusively to infer nested types
    within `Optional`, `Union` types, for the cleanest possible string
    representation of a type.

    Args:
        cls: The type to convert to a text representation.

    Returns:
        A clean, human-readable string representation of the type.
    """
    # Handle None type
    if cls is None or cls is type(None):
        return "None"

    # Get origin and args using typing_inspect for better type handling
    origin = inspection.get_origin(cls)
    args = inspection.get_args(cls)

    if origin is not None:
        # Handle Optional (Union[T, None])
        if inspection.is_optional_type(cls):
            # Recursively get the name of the inner type (the one not None)
            inner_type = args[0]
            inner_type_name = convert_type_to_text(inner_type)
            return f"Optional[{inner_type_name}]"

        # Handle other Union types
        if inspection.is_union_type(cls):
            # Recursively get names of all arguments in the Union
            args_str = ", ".join(convert_type_to_text(arg) for arg in args)
            return f"Union[{args_str}]"

        # Handle other generic types (List, Dict, Tuple, Set, etc.)
        # Use origin.__name__ for built-in generics like list, dict, tuple, set
        origin_name = getattr(origin, "__name__", str(origin).split(".")[-1])
        if origin_name.startswith("_"):  # Handle internal typing names like _List
            origin_name = origin_name[1:]

        # Convert to lowercase for built-in types to match modern Python style
        if origin_name in ["List", "Dict", "Tuple", "Set"]:
            origin_name = origin_name.lower()

        if args:  # If there are type arguments
            # Recursively get names of type arguments
            args_str = ", ".join(convert_type_to_text(arg) for arg in args)
            return f"{origin_name}[{args_str}]"
        else:  # Generic without arguments (e.g., typing.List)
            return origin_name

    # Handle special cases with typing_inspect
    if inspection.is_typevar(cls):
        return str(cls)
    if inspection.is_forward_ref(cls):
        return str(cls)
    if inspection.is_literal_type(cls):
        return f"Literal[{', '.join(str(arg) for arg in args)}]"
    if inspection.is_final_type(cls):
        return f"Final[{convert_type_to_text(args[0])}]" if args else "Final"
    if inspection.is_new_type(cls):
        return str(cls)

    # Handle Pydantic BaseModel types
    if is_pydantic_basemodel(cls):
        if hasattr(cls, "__name__"):
            return cls.__name__
        return "BaseModel"

    # Handle msgspec Struct types
    if is_msgspec_struct(cls):
        if hasattr(cls, "__name__"):
            return cls.__name__
        return "Struct"

    # Handle dataclass types
    if is_dataclass(cls):
        if hasattr(cls, "__name__"):
            return cls.__name__
        return "dataclass"

    # Handle basic types with __name__ attribute
    if hasattr(cls, "__name__") and cls.__name__ != "<lambda>":
        return cls.__name__

    # Special handling for Optional type string representation
    if str(cls).startswith("typing.Optional"):
        # Extract the inner type from the string representation
        inner_type_str = str(cls).replace("typing.Optional[", "").rstrip("]")
        return f"Optional[{inner_type_str}]"

    # Fallback for any other types
    # Clean up 'typing.' prefix and handle other common representations
    return str(cls).replace("typing.", "").replace("__main__.", "")


def convert_docstring_to_text(
    obj: Any,
    *,
    params_override: Optional[str] = None,
    returns_override: Optional[str] = None,
    raises_override: Optional[str] = None,
    examples_override: Optional[str] = None,
    params_prefix: Optional[str] = None,
    returns_prefix: Optional[str] = None,
    raises_prefix: Optional[str] = None,
    exclude_params: bool = False,
    exclude_returns: bool = False,
    exclude_raises: bool = False,
    exclude_examples: bool = False,
) -> str:
    """
    Convert an object's docstring to formatted text using docstring_parser.

    Args:
        obj: The object to extract docstring from
        params_override: Override text for parameters section
        returns_override: Override text for returns section
        raises_override: Override text for raises section
        examples_override: Override text for examples section
        params_prefix: Prefix for parameters section
        returns_prefix: Prefix for returns section
        raises_prefix: Prefix for raises section
        exclude_params: Whether to exclude parameters section
        exclude_returns: Whether to exclude returns section
        exclude_raises: Whether to exclude raises section
        exclude_examples: Whether to exclude examples section

    Returns:
        Formatted text representation of the docstring
    """
    # Get the raw docstring
    doc = getattr(obj, "__doc__", None)
    if not doc:
        return ""

    try:
        # Parse the docstring using docstring_parser
        parsed = parse(doc)

        parts = []

        # Add short description
        if parsed.short_description:
            parts.append(parsed.short_description)

        # Add long description
        if parsed.long_description:
            parts.append("")  # Empty line separator
            parts.append(parsed.long_description)

        # Add parameters section
        if not exclude_params and (params_override or parsed.params):
            parts.append("")  # Empty line separator
            if params_override:
                parts.append(params_override)
            else:
                prefix = params_prefix or "Parameters:"
                parts.append(prefix)
                for param in parsed.params:
                    param_line = f"  {param.arg_name}"
                    if param.type_name:
                        param_line += f" ({param.type_name})"
                    if param.description:
                        param_line += f": {param.description}"
                    parts.append(param_line)

        # Add returns section
        if not exclude_returns and (returns_override or parsed.returns):
            parts.append("")  # Empty line separator
            if returns_override:
                parts.append(returns_override)
            else:
                prefix = returns_prefix or "Returns:"
                parts.append(prefix)
                if parsed.returns:
                    return_line = "  "
                    if parsed.returns.type_name:
                        return_line += f"{parsed.returns.type_name}: "
                    if parsed.returns.description:
                        return_line += parsed.returns.description
                    parts.append(return_line)

        # Add raises section
        if not exclude_raises and (raises_override or parsed.raises):
            parts.append("")  # Empty line separator
            if raises_override:
                parts.append(raises_override)
            else:
                prefix = raises_prefix or "Raises:"
                parts.append(prefix)
                for exc in parsed.raises:
                    exc_line = f"  {exc.type_name or 'Exception'}"
                    if exc.description:
                        exc_line += f": {exc.description}"
                    parts.append(exc_line)

        # Add examples section (if available in parsed docstring)
        if not exclude_examples and examples_override:
            parts.append("")  # Empty line separator
            parts.append(examples_override)

        return "\n".join(parts)

    except Exception:
        # Fallback to raw docstring if parsing fails
        return doc.strip()


def convert_dataclass_to_text(
    obj: Any,
    title: Optional[str],
    description: Optional[str],
    table_format: bool,
    show_types: bool,
    show_defaults: bool,
    show_values: bool,
    indent_level: int,
) -> str:
    """Convert a dataclass to Markdown format."""
    is_class = isinstance(obj, type)
    obj_name = title or (obj.__name__ if is_class else obj.__class__.__name__)

    parts = []
    parts.append(markdown_heading(obj_name, min(indent_level + 1, 6)))

    if description:
        parts.append(f"\n{description}\n")

    fields_data = []
    for field in dataclass_fields(obj if is_class else obj.__class__):
        field_info = {
            "name": field.name,
            "type": convert_type_to_text(field.type) if show_types else None,
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

        parts.append("\n" + markdown_table_row(headers, is_header=True))

        # Add rows
        for field_info in fields_data:
            row = [markdown_code(field_info["name"])]
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
            parts.append(markdown_table_row(row))
    else:
        # List format
        for field_info in fields_data:
            field_desc = markdown_code(field_info["name"])
            if field_info["type"]:
                field_desc += f" ({field_info['type']})"
            if field_info["default"] is not None:
                field_desc += f" - default: {field_info['default']}"
            if field_info["value"] is not None:
                field_desc += f" = {field_info['value']}"
            parts.append(markdown_list_item(field_desc, indent_level))

    return "\n".join(parts)


def convert_pydantic_to_text(
    obj: Any,
    title: Optional[str],
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

    obj_name = title or (obj.__name__ if is_class else obj.__class__.__name__)

    parts = []
    parts.append(markdown_heading(obj_name, min(indent_level + 1, 6)))

    if description:
        parts.append(f"\n{description}\n")

    model_fields = getattr(obj if is_class else obj.__class__, "model_fields", {})
    fields_data = []

    for field_name, field_info in model_fields.items():
        field_data = {
            "name": field_name,
            "type": convert_type_to_text(field_info.annotation) if show_types else None,
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

        parts.append("\n" + markdown_table_row(headers, is_header=True))

        for field_data in fields_data:
            row = [markdown_code(field_data["name"])]
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
            parts.append(markdown_table_row(row))
    else:
        # List format
        for field_data in fields_data:
            field_desc = markdown_code(field_data["name"])
            if field_data["type"]:
                field_desc += f" ({field_data['type']})"
            if field_data["required"] is not None:
                field_desc += (
                    " " + markdown_bold("[Required]")
                    if field_data["required"]
                    else " " + markdown_italic("[Optional]")
                )
            if field_data["default"] is not None:
                field_desc += f" - default: {field_data['default']}"
            if field_data["value"] is not None:
                field_desc += f" = {field_data['value']}"

            parts.append(markdown_list_item(field_desc, indent_level))

            if field_data["description"]:
                parts.append(
                    markdown_list_item(field_data["description"], indent_level + 1)
                )

    return "\n".join(parts)


def convert_function_to_text(
    obj: Callable,
    title: Optional[str],
    description: Optional[str],
    show_signature: bool,
    show_docstring: bool,
    indent_level: int,
) -> str:
    """Convert a function to Markdown format."""
    func_name = title or obj.__name__

    parts = []
    parts.append(markdown_heading(func_name, min(indent_level + 1, 6)))

    if show_signature:
        import inspect

        try:
            sig = inspect.signature(obj)
            parts.append(f"\n{markdown_code(f'{func_name}{sig}')}\n")
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


def convert_collection_to_text(
    obj: Union[List, Set, tuple],
    title: Optional[str],
    description: Optional[str],
    compact: bool,
    show_indices: bool,
    indent_level: int,
    visited: Set[int],
) -> str:
    """Convert a collection to Markdown format."""
    obj_name = title or obj.__class__.__name__

    parts = []
    if not compact:
        parts.append(markdown_heading(obj_name, min(indent_level + 1, 6)))
        if description:
            parts.append(f"\n{description}\n")

    if not obj:
        parts.append(markdown_italic("(empty)"))
        return "\n".join(parts)

    for i, item in enumerate(obj):
        if show_indices:
            item_text = f"[{i}] {convert_to_text(item, compact=True, _visited=visited)}"
        else:
            item_text = convert_to_text(item, compact=True, _visited=visited)
        parts.append(markdown_list_item(item_text, indent_level))

    return "\n".join(parts)


def convert_dict_to_text(
    obj: Dict[Any, Any],
    title: Optional[str],
    description: Optional[str],
    table_format: bool,
    compact: bool,
    indent_level: int,
    visited: Set[int],
) -> str:
    """Convert a dictionary to Markdown format."""
    obj_name = title or "Dictionary"

    parts = []
    if not compact:
        parts.append(markdown_heading(obj_name, min(indent_level + 1, 6)))
        if description:
            parts.append(f"\n{description}\n")

    if not obj:
        parts.append(markdown_italic("(empty)"))
        return "\n".join(parts)

    if table_format and all(
        isinstance(v, (str, int, float, bool, type(None))) for v in obj.values()
    ):
        # Use table format for simple values
        parts.append("\n" + markdown_table_row(["Key", "Value"], is_header=True))
        for key, value in obj.items():
            parts.append(markdown_table_row([markdown_code(str(key)), str(value)]))
    else:
        # Use list format
        for key, value in obj.items():
            key_str = markdown_code(str(key))
            value_str = convert_to_text(value, compact=True, _visited=visited)
            parts.append(markdown_list_item(f"{key_str}: {value_str}", indent_level))

    return "\n".join(parts)


# -----------------------------------------------------------------------------
# Main Converter Function
# -----------------------------------------------------------------------------


def convert_to_text(
    obj: Any,
    *,
    # Formatting options
    title: Optional[str] = None,
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
        return markdown_italic("(circular reference)")

    visited_copy = visited.copy()
    visited_copy.add(obj_id)

    # Handle None
    if obj is None:
        return markdown_code("None")

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        text = str(obj)
        if escape_special_chars and isinstance(obj, str):
            text = _escape_markdown(text)
        return text if compact else markdown_code(text)

    # Handle bytes
    if isinstance(obj, bytes):
        return markdown_code(f"b'{obj.hex()}'")

    # Wrap in code block if requested
    if code_block_language:
        try:
            if code_block_language.lower() == "json":
                content = json.dumps(obj, indent=2)
            else:
                content = str(obj)
            return markdown_code_block(content, code_block_language)
        except Exception:
            pass

    result = ""

    # Handle dataclasses
    if is_dataclass(obj):
        result = convert_dataclass_to_text(
            obj,
            title,
            description,
            table_format,
            show_types,
            show_defaults,
            show_values,
            _indent_level,
        )

    # Handle Pydantic models
    elif is_pydantic_basemodel(obj):
        result = convert_pydantic_to_text(
            obj,
            title,
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
        result = convert_dataclass_to_text(
            obj,
            title,
            description,
            table_format,
            show_types,
            show_defaults,
            show_values,
            _indent_level,
        )

    # Handle functions
    elif callable(obj) and hasattr(obj, "__name__"):
        result = convert_function_to_text(
            obj, title, description, show_signature, show_docstring, _indent_level
        )

    # Handle collections
    elif isinstance(obj, (list, tuple, set)):
        result = convert_collection_to_text(
            obj, title, description, compact, show_indices, _indent_level, visited_copy
        )

    # Handle dictionaries
    elif isinstance(obj, dict):
        result = convert_dict_to_text(
            obj, title, description, table_format, compact, _indent_level, visited_copy
        )

    # Default handling
    else:
        obj_name = title or obj.__class__.__name__
        parts = []
        if not compact:
            parts.append(markdown_heading(obj_name, min(_indent_level + 1, 6)))
            if description:
                parts.append(f"\n{description}\n")
        parts.append(markdown_code(str(obj)))
        result = "\n".join(parts)

    # Add horizontal rule if requested
    if add_horizontal_rules and not compact and _indent_level == 0:
        result += f"\n\n{markdown_horizontal_rule()}\n"

    return result
