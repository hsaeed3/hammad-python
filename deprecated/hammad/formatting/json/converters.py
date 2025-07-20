"""hammad.formatting.json.converters

Contains various utility functions used when working with JSON data."""

import dataclasses
from typing import Any
import msgspec
from msgspec.json import encode as encode_json, decode as decode_json

from ...typing import get_type_description, inspection  # type: ignore

__all__ = (
    "SchemaError",
    "convert_to_json_schema",
    "encode",
    "decode",
)


class SchemaError(Exception):
    """An exception raised when a schema utility raises an error."""


def convert_to_json_schema(t: Any) -> dict:
    """Converts various objects, types, and interfaces into
    a JSON schema.

    Args:
        t: The object, type, or interface to convert to a JSON schema.

    Returns:
        A JSON schema as a dictionary.
    """
    from dataclasses import is_dataclass, fields as dataclass_fields
    import inspect
    from typing import get_type_hints

    schema = {"type": "object", "properties": {}}

    # Handle msgspec Struct
    try:
        if isinstance(t, type) and issubclass(t, msgspec.Struct):
            struct_info = msgspec.structs.fields(t)
            for field in struct_info:
                field_type = field.type
                field_schema = {
                    "type": get_type_description(field_type),
                    "description": f"Field of type {get_type_description(field_type)}",
                }
                if field.default is not msgspec.NODEFAULT:
                    field_schema["default"] = field.default
                schema["properties"][field.name] = field_schema
            return schema
    except (ImportError, AttributeError):
        pass

    # Handle Pydantic models
    try:
        from pydantic import BaseModel

        if isinstance(t, type) and issubclass(t, BaseModel):
            pydantic_schema = (
                t.model_json_schema() if hasattr(t, "model_json_schema") else t.schema()
            )
            return pydantic_schema
    except ImportError:
        pass

    # Handle dataclasses
    if is_dataclass(t):
        if isinstance(t, type):
            # Class-level dataclass
            for field in dataclass_fields(t):
                field_type = field.type
                field_schema = {
                    "type": get_type_description(field_type),
                    "description": f"Field of type {get_type_description(field_type)}",
                }
                if field.default is not dataclasses.MISSING:
                    field_schema["default"] = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    field_schema["default"] = "factory function"
                schema["properties"][field.name] = field_schema
        else:
            # Instance-level dataclass
            for field in dataclass_fields(t):
                field_type = field.type
                field_schema = {
                    "type": get_type_description(field_type),
                    "description": f"Field of type {get_type_description(field_type)}",
                    "value": getattr(t, field.name, None),
                }
                schema["properties"][field.name] = field_schema
        return schema

    # Handle regular classes with type hints (including abstract classes)
    if inspect.isclass(t):
        try:
            type_hints = get_type_hints(t)
            for name, type_hint in type_hints.items():
                schema["properties"][name] = {
                    "type": get_type_description(type_hint),
                    "description": f"Field of type {get_type_description(type_hint)}",
                }
        except (NameError, AttributeError):
            pass
        return schema

    # Handle dictionary
    if isinstance(t, dict):
        for key, value in t.items():
            schema["properties"][key] = {
                "type": type(value).__name__,
                "description": f"Field of type {type(value).__name__}",
                "example": value,
            }
        return schema

    # Handle basic types and type hints
    origin = inspection.get_origin(t)
    if origin is not None:
        args = inspection.get_args(t)
        if origin is list and args:
            return {"type": "array", "items": {"type": get_type_description(args[0])}}
        elif origin is dict and len(args) == 2:
            return {
                "type": "object",
                "additionalProperties": {"type": get_type_description(args[1])},
                "description": f"Object with {get_type_description(args[0])} keys",
            }
        elif origin is tuple and args:
            return {
                "type": "array",
                "items": [{"type": get_type_description(arg)} for arg in args],
                "minItems": len(args),
                "maxItems": len(args),
            }
        elif inspection.is_union_type(t):
            if inspection.is_optional_type(t):
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    return {
                        "type": get_type_description(non_none_args[0]),
                        "nullable": True,
                    }
            else:
                return {"anyOf": [{"type": get_type_description(arg)} for arg in args]}
        elif inspection.is_literal_type(t) and args:
            return {"enum": list(args)}

    # Default to string representation of type
    return {"type": get_type_description(t)}


def convert_to_json(
    target: Any,
) -> str:
    return encode_json(target).decode()
