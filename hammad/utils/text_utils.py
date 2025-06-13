"""hammad.utils.text_utils"""

import json
import logging
from dataclasses import (
    is_dataclass,
    fields as dataclass_fields
)
from docstring_parser import parse
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    get_args
)

from ..utils.json_utils import convert_to_json_schema
from ..types._utils import (
    inspection,
    is_pydantic_basemodel,
    is_pydantic_basemodel_instance,
    is_msgspec_struct,
    get_type_description
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------
# Converters
# ------------------------------------------------------------------------


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
    obj : Any,
    *,
    params_override : Optional[str] = None,
    returns_override : Optional[str] = None,
    raises_override : Optional[str] = None,
    examples_override : Optional[str] = None,
    params_prefix : Optional[str] = None,
    returns_prefix : Optional[str] = None,
    raises_prefix : Optional[str] = None,
    exclude_params : bool = False,
    exclude_returns : bool = False,
    exclude_raises : bool = False,
    exclude_examples : bool = False,
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


# ------------------------------------------------------------------------
# PRIMARY METHOD
# ------------------------------------------------------------------------


def convert_to_text(
    obj : Any,
    *,
    # ------------------------------------------------------------
    # Override Params
    # ------------------------------------------------------------
    prefix : str = "",
    suffix : str = "",
    title : str | None = None,
    description : str | None = None,
    examples : str | list[str] | None = None,
    # ------------------------------------------------------------
    # Primary Formatting Params
    # ------------------------------------------------------------
    code_block : bool = False,
    compact : bool = False,
    indent : int = 0,
    bullet_style : Literal["-", "*", "+", ">"] | str = "-",
    title_style : Literal["<>", "[]", "{}", "#"] | str = "##",
    # ------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------
    show_types : bool = True,
    show_values : bool = True,
    show_capital_titles : bool = False,
    show_description : bool = True,
    show_field_descriptions : bool = True,
    show_examples : bool = True,
    show_defaults : bool = True,
    show_required : bool = True,
    show_json_schema : bool = True,
    # ------------------------------------------------------------
    # Internal params for recursion
    # ------------------------------------------------------------
    _visited : set[int] | None = None,
) -> str:
    """Converts any target object into a cleanly formatted text representation.
    
    Args:
        - t (Any) : The target object to convert to text.
        - prefix (str) : A prefix to add at the beginning of the text string.
        - suffix (str) : A suffix to add at the end of the text string.
        - title (str | None) : Either an explicit title to add, or an override for the object's title.
        - description (str | None) : Either an explicit description to add, or an override for the object's description / doc.
        - examples (str | list[str] | None) : Either an explicit list of examples to add, or an override for the object's examples.
        - code_block (bool) : Whether to format the text as a code block. (This will use JSON Schema for the content for functions / models.)
        - compact (bool) : Whether to format the text in a compact manner. This does not just mean it will 'compact' the block, but rather the
            object will be formatted in natural language. Furthermore the content of this object will vary based on if the input
            is a class / instance, as well as if it is either a function, etc. (E.g. For a class that is not an instance yet like a Pydantic Model,
            the content will be explained as a schema.)
                This is a very powerful parameter can changes many aspects of the output.
                EX: With compact = False:
                ```bash
                # >>> SomeModel
                # >>>     - Name : (String)
                # >>>		  - Name is an **OPTIONAL FIELD**
                # >>>         - Name is currently is not defined with a value
                # >>>         - Name has a default value of "John"
                # >>>     - Age : (Integer)
                # >>>         - Age is an **OPTIONAL FIELD**
                # >>>         - Age is currently is not defined with a value
                # >>>         - Age has a default value of 20
                ```
                With compact = True:
                ```bash
                # >>> SomeModel:
                # >>> The SomeModel schema currently has 2 fields, defined as Name (String) and Age (Integer).
                # >>> - The Name field does not have a value, and has a default value of "John"
                # >>> - The Age field does not have a value, and has a default value of 20
                ```
        - indent (int) : The number of spaces to indent the text.
        - bullet_style (Literal["-", "*", "+", ">"] | str) : The style of bullet to use for the text.
        - title_style (Literal["<>", "[]", "{}", "#"] | str) : The style of title to use for the text.
        - show_types (bool) : Whether to show the types of the fields.
        - show_values (bool) : Whether to show the values of the fields. (Both a description of if it has a value defined, and what the valye is)
        - show_capital_titles (bool) : Whether to show the titles in capital letters.
        - show_description (bool) : Whether to show the description of the object.
        - show_field_descriptions (bool) : Whether to show the descriptions of the fields.
        - show_examples (bool) : Whether to show the examples of the object.
        - show_defaults (bool) : Whether to show the default values of the fields.
        - show_required (bool) : Whether to show the required fields.
        - show_json_schema (bool) : Whether to show the JSON Schema of the object.
        
        Returns:
            A cleanly formatted text representation of the target object.
        """
    # Initialize visited set for circular reference detection
    visited = _visited if _visited is not None else set()
    obj_id = id(obj)
    
    # Check for circular references
    if obj_id in visited:
        return "<circular>"
    
    # Add current object to visited set for recursive calls
    visited_copy = visited.copy()
    visited_copy.add(obj_id)
    
    # Setup indentation and bullet styling
    prefix_indent = "  " * indent
    bullet = f"{bullet_style} " if bullet_style else ""
    
    # Helper function to format title with title_style
    def format_title(title_text: str) -> str:
        if not title_text:
            return ""
        
        if show_capital_titles:
            title_text = title_text.upper()
            
        if title_style == "<>":
            return f"<{title_text}>"
        elif title_style == "[]":
            return f"[{title_text}]"
        elif title_style == "{}":
            return f"{{{title_text}}}"
        elif title_style == "#":
            return f"# {title_text}"
        elif title_style == "##":
            return f"## {title_text}"
        else:
            return title_text
    
    # Helper function for recursive calls
    def _recursive_convert(
        target: Any, 
        new_indent: int = 0,
        override_title: str = None,
        override_show_title: bool = None,
        override_show_bullets: bool = None,
        override_show_values: bool = None
    ) -> str:
        return convert_to_text(
            target,
            indent=new_indent,
            code_block=False,  # Usually don't nest code blocks
            compact=compact,
            show_types=show_types,
            show_values=override_show_values if override_show_values is not None else show_values,
            show_capital_titles=show_capital_titles,
            show_description=show_description,
            show_field_descriptions=show_field_descriptions,
            show_examples=False,  # Don't show examples for nested items
            show_defaults=show_defaults,
            show_required=show_required,
            show_json_schema=show_json_schema,
            bullet_style=bullet_style,
            title_style=title_style,
            title=override_title,
            _visited=visited_copy
        )
    
    # Handle primitive types and bytes
    if obj is None:
        result = "None"
    elif isinstance(obj, (str, int, float, bool)):
        result = str(obj)
    elif isinstance(obj, bytes):
        result = f"b'{obj.hex()}'"
    
    # Handle dataclasses (before callable check since dataclass classes are callable)
    elif is_dataclass(obj):
        is_class = isinstance(obj, type)
        
        obj_name = title or (obj.__name__ if is_class else obj.__class__.__name__)
        
        if code_block and show_json_schema:
            try:
                schema = convert_to_json_schema(obj)
                result = f"```json\n{json.dumps(schema, indent=2)}\n```"
            except Exception:
                if is_class or not show_values:
                    # Show schema
                    data = {}
                    for field in dataclass_fields(obj):
                        type_name = convert_type_to_text(field.type)
                        data[field.name] = type_name
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
                else:
                    # Show values
                    data = {field.name: getattr(obj, field.name) for field in dataclass_fields(obj)}
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
        else:
            # Text formatting
            header_parts = []
            formatted_title = format_title(obj_name)
            if formatted_title:
                header_parts.append(f"{prefix_indent}{bullet}**{formatted_title}**:")
            
            if show_description:
                desc = description or convert_docstring_to_text(obj if is_class else obj.__class__)
                if desc:
                    header_parts.append(f"{prefix_indent}  {desc}")
            
            field_lines = []
            field_indent = indent + (1 if not compact else 0)
            
            # Only show fields if we have any show flags enabled that would display field info
            show_field_info = (show_types or show_values or show_defaults or show_required or 
                             show_field_descriptions or is_class)
            
            if show_field_info:
                for field in dataclass_fields(obj):
                    field_parts = []
                    type_name = convert_type_to_text(field.type) if show_types else ""
                    type_info = f": {type_name}" if type_name else ""
                    
                    # Check if field has default
                    import dataclasses
                    has_default = field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING
                    
                    if compact:
                        field_desc = f"{field.name}{type_info}"
                        if show_values and not is_class:
                            value = getattr(obj, field.name)
                            field_desc += f" = {value}"
                        elif show_defaults and has_default:
                            if field.default is not dataclasses.MISSING:
                                field_desc += f" (default: {field.default})"
                            else:
                                field_desc += " (default: factory)"
                        field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field_desc}")
                    else:
                        field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field.name}{type_info}")
                        
                        if show_required:
                            req_text = "OPTIONAL FIELD" if has_default else "REQUIRED FIELD"
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- {req_text}")
                        
                        if show_values and not is_class:
                            value = getattr(obj, field.name)
                            formatted_value = _recursive_convert(
                                value, 
                                field_indent + 2,
                                override_show_title=False,
                                override_show_bullets=False
                            )
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Current value: {formatted_value}")
                        
                        if show_defaults and has_default:
                            if field.default is not dataclasses.MISSING:
                                field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Default: {field.default}")
                            else:
                                field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Default: factory function")
                    
                    field_lines.extend(field_parts)
            
            result = "\n".join(header_parts + field_lines)
    
    elif callable(obj) and hasattr(obj, '__name__'):
        # Handle functions/methods
        func_name = title or obj.__name__
        if code_block and show_json_schema:
            try:
                schema = convert_to_json_schema(obj)
                result = f"```json\n{json.dumps(schema, indent=2)}\n```"
            except Exception:
                result = f"Function: {func_name}"
        else:
            header_parts = []
            if show_description:
                desc = description or convert_docstring_to_text(obj)
                if desc:
                    header_parts.append(desc)
            
            formatted_title = format_title(func_name)
            result = f"{formatted_title}\n{chr(10).join(header_parts)}" if header_parts else formatted_title
    
    # Handle Pydantic models
    elif is_pydantic_basemodel(obj):
        is_class = isinstance(obj, type)
        is_instance = is_pydantic_basemodel_instance(obj)
        
        # Determine object name
        obj_name = title or (obj.__name__ if is_class else obj.__class__.__name__)
        
        if code_block and show_json_schema:
            try:
                schema = convert_to_json_schema(obj)
                result = f"```json\n{json.dumps(schema, indent=2)}\n```"
            except Exception:
                if is_class or not show_values:
                    # Show schema
                    data = {}
                    model_fields = getattr(obj if is_class else obj.__class__, 'model_fields', {})
                    for field, field_info in model_fields.items():
                        type_name = convert_type_to_text(field_info.annotation)
                        data[field] = type_name
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
                else:
                    # Show values
                    data = obj.model_dump() if hasattr(obj, 'model_dump') else {}
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
        else:
            # Text formatting
            header_parts = []
            formatted_title = format_title(obj_name)
            if formatted_title:
                header_parts.append(f"{prefix_indent}{bullet}**{formatted_title}**:")
            
            # Add description
            if show_description:
                desc = description or convert_docstring_to_text(obj if is_class else obj.__class__)
                if desc:
                    header_parts.append(f"{prefix_indent}  {desc}")
            
            # Handle fields
            field_lines = []
            model_fields = getattr(obj if is_class else obj.__class__, 'model_fields', {})
            field_indent = indent + (1 if not compact else 0)
            
            for field_name, field_info in model_fields.items():
                field_parts = []
                type_name = convert_type_to_text(field_info.annotation) if show_types else ""
                type_info = f": {type_name}" if type_name else ""
                
                # Determine if this is required field
                is_required = getattr(field_info, 'is_required', lambda: True)()
                has_default = hasattr(field_info, 'default') and field_info.default is not None
                
                if compact:
                    # Compact format - single line description
                    field_desc = f"{field_name}{type_info}"
                    
                    if show_values and is_instance:
                        value = getattr(obj, field_name, "<missing>")
                        field_desc += f" = {value}"
                    elif show_defaults and has_default:
                        field_desc += f" (default: {field_info.default})"
                    
                    if show_required and is_required:
                        field_desc += " [REQUIRED]"
                    
                    field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field_desc}")
                else:
                    # Detailed format
                    field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field_name}{type_info}")
                    
                    if show_field_descriptions:
                        # Try to get field description
                        desc = getattr(field_info, 'description', None)
                        if desc:
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- {desc}")
                    
                    if show_required:
                        req_text = "REQUIRED FIELD" if is_required else "OPTIONAL FIELD"
                        field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- {req_text}")
                    
                    if show_values and is_instance:
                        value = getattr(obj, field_name, "<missing>")
                        if value != "<missing>":
                            formatted_value = _recursive_convert(
                                value, 
                                field_indent + 2,
                                override_show_title=False,
                                override_show_bullets=False
                            )
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Current value: {formatted_value}")
                        else:
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- No value set")
                    
                    if show_defaults and has_default:
                        field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Default: {field_info.default}")
                
                field_lines.extend(field_parts)
            
            if compact and field_lines:
                # For compact mode, might want to inline fields
                content = "\n".join(header_parts + field_lines)
            else:
                content = "\n".join(header_parts + field_lines)
            
            result = content
    
    # Handle msgspec structs
    elif is_msgspec_struct(obj):
        is_class = isinstance(obj, type)
        
        obj_name = title or (obj.__name__ if is_class else obj.__class__.__name__)
        
        if code_block and show_json_schema:
            try:
                schema = convert_to_json_schema(obj)
                result = f"```json\n{json.dumps(schema, indent=2)}\n```"
            except Exception:
                if is_class or not show_values:
                    # Show schema
                    data = {}
                    struct_fields = getattr(obj if is_class else obj.__class__, '__struct_fields__', ())
                    annotations = getattr(obj if is_class else obj.__class__, '__annotations__', {})
                    for field_name in struct_fields:
                        field_type = annotations.get(field_name, Any)
                        type_name = convert_type_to_text(field_type)
                        data[field_name] = type_name
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
                else:
                    # Show values
                    data = {}
                    for field_name in obj.__struct_fields__:
                        data[field_name] = getattr(obj, field_name, None)
                    result = f"```json\n{json.dumps(data, indent=2)}\n```"
        else:
            # Text formatting similar to Pydantic
            header_parts = []
            formatted_title = format_title(obj_name)
            if formatted_title:
                header_parts.append(f"{prefix_indent}{bullet}**{formatted_title}**:")
            
            if show_description:
                desc = description or convert_docstring_to_text(obj if is_class else obj.__class__)
                if desc:
                    header_parts.append(f"{prefix_indent}  {desc}")
            
            field_lines = []
            struct_fields = getattr(obj if is_class else obj.__class__, '__struct_fields__', ())
            annotations = getattr(obj if is_class else obj.__class__, '__annotations__', {})
            field_indent = indent + (1 if not compact else 0)
            
            for field_name in struct_fields:
                field_parts = []
                field_type = annotations.get(field_name, Any)
                type_name = convert_type_to_text(field_type) if show_types else ""
                type_info = f": {type_name}" if type_name else ""
                
                if compact:
                    field_desc = f"{field_name}{type_info}"
                    if show_values and not is_class:
                        value = getattr(obj, field_name, "<missing>")
                        field_desc += f" = {value}"
                    field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field_desc}")
                else:
                    field_parts.append(f"{prefix_indent}{'  ' * field_indent}{bullet}{field_name}{type_info}")
                    
                    if show_values and not is_class:
                        value = getattr(obj, field_name, "<missing>")
                        if value != "<missing>":
                            formatted_value = _recursive_convert(
                                value, 
                                field_indent + 2,
                                override_show_title=False,
                                override_show_bullets=False
                            )
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- Current value: {formatted_value}")
                        else:
                            field_parts.append(f"{prefix_indent}{'  ' * (field_indent + 1)}- No value set")
                
                field_lines.extend(field_parts)
            
            result = "\n".join(header_parts + field_lines)
    
    # Handle collections (list, tuple, set)
    elif isinstance(obj, (list, tuple, set)):
        if not obj:
            result = "[]" if isinstance(obj, list) else "()" if isinstance(obj, tuple) else "{}"
        else:
            collection_name = title or (obj.__class__.__name__ if show_types else "Collection")
            
            if code_block:
                # Try to serialize as JSON
                try:
                    data_to_dump = []
                    for item in obj:
                        if is_pydantic_basemodel(item):
                            data_to_dump.append(item.model_dump() if hasattr(item, 'model_dump') else str(item))
                        elif is_msgspec_struct(item):
                            data = {field: getattr(item, field, None) for field in item.__struct_fields__}
                            data_to_dump.append(data)
                        elif isinstance(item, dict):
                            data_to_dump.append(item)
                        else:
                            data_to_dump.append(item)
                    result = f"```json\n{json.dumps(data_to_dump, indent=2)}\n```"
                except Exception:
                    # Fallback to text representation
                    items_str = ", ".join(str(item) for item in obj)
                    result = f"[{items_str}]"
            else:
                header_parts = []
                formatted_title = format_title(collection_name)
                if formatted_title:
                    header_parts.append(f"{prefix_indent}{bullet}**{formatted_title}**:")
                
                # Add description if provided
                if show_description and description:
                    header_parts.append(f"{prefix_indent}  {description}")
                
                item_lines = []
                item_indent = indent + (1 if compact else 2)
                
                for item in obj:
                    formatted_item = _recursive_convert(
                        item, 
                        item_indent,
                        override_show_title=True,
                        override_show_bullets=True
                    )
                    item_lines.append(formatted_item)
                
                result = "\n".join(header_parts + item_lines)
    
    # Handle dictionaries
    elif isinstance(obj, dict):
        if not obj:
            result = "{}"
        else:
            dict_name = title or (obj.__class__.__name__ if show_types else "Dictionary")
            
            if code_block:
                try:
                    result = f"```json\n{json.dumps(obj, indent=2)}\n```"
                except Exception:
                    result = str(obj)
            else:
                header_parts = []
                formatted_title = format_title(dict_name)
                if formatted_title:
                    header_parts.append(f"{prefix_indent}{bullet}**{formatted_title}**:")
                
                # Add description if provided
                if show_description and description:
                    header_parts.append(f"{prefix_indent}  {description}")
                
                item_lines = []
                item_indent = indent + (1 if compact else 2)
                
                for key, value in obj.items():
                    formatted_value = _recursive_convert(
                        value, 
                        item_indent + 1,
                        override_show_title=False,
                        override_show_bullets=False
                    )
                    item_lines.append(f"{prefix_indent}{'  ' * item_indent}{bullet}{key}: {formatted_value}")
                
                result = "\n".join(header_parts + item_lines)
    
    # Fallback for other types
    else:
        type_name = title or convert_type_to_text(type(obj))
        if code_block and show_json_schema:
            try:
                schema = convert_to_json_schema(obj)
                result = f"```json\n{json.dumps(schema, indent=2)}\n```"
            except Exception:
                result = str(obj)
        else:
            result = f"{format_title(type_name)}: {str(obj)}" if type_name else str(obj)
    
    # Add examples if provided
    final_parts = [result] if result else []
    
    if show_examples and examples:
        final_parts.append("")  # Empty line
        if isinstance(examples, list):
            final_parts.append("Examples:")
            for i, example in enumerate(examples, 1):
                final_parts.append(f"{prefix_indent}  {i}. {example}")
        else:
            final_parts.append(f"Example: {examples}")
    
    # Join all parts
    final_result = "\n".join(final_parts)
    
    # Apply prefix and suffix
    if prefix:
        final_result = f"{prefix}{final_result}"
    if suffix:
        final_result = f"{final_result}{suffix}"
    
    return final_result