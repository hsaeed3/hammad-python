"""hammad.text.utils.converters"""

from docstring_parser import parse
from typing import (
    Any,
    Optional,
)

from ...typing import (
    inspection,
    is_pydantic_basemodel,
    is_msgspec_struct,
    is_dataclass,
)

__all__ = [
    "convert_type_to_text",
    "convert_docstring_to_text",
]


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
