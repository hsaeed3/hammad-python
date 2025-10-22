"""ham.inspection.typing

Inspection utilities for 'raw' / built-in Python types."""

import typing
from typing import is_typeddict, is_protocol
from inspect import isclass, isfunction as is_function
from enum import Enum

import typing_inspect
from typing_inspect import (
    is_literal_type,
    is_union_type,
    is_optional_type,
)
from pydantic import BaseModel


__all__ = (
    "is_simple_type",
    "get_type_description",
    "get_standardized_type_name",
    "get_literal_type_values",
    "is_value_in_literal_type",
    "get_enum_type_values",
    "is_key_in_enum_type",
    "is_value_in_enum_type",
    "is_typeddict",
    "is_protocol",
    "is_function",
    "is_union_type",
    "is_literal_type",
    "is_optional_type",
)


def _validateIsSubClass(response_model: type):
    """
    Temporary guard against issues with generics in Python 3.9
    """
    import sys

    if sys.version_info < (3, 10):
        if len(typing.get_args(response_model)) == 0:
            return False
        return issubclass(typing.get_args(response_model)[0], BaseModel)
    try:
        # Add a guard here to prevent issues with GenericAlias
        import types

        if isinstance(response_model, types.GenericAlias):
            return False
    except Exception:
        pass

    return issubclass(response_model, BaseModel)


def is_simple_type(
    t: type[BaseModel] | str | int | float | bool | typing.Any,
) -> bool:
    """Determines if a type hint is a 'simple type'.

    NOTE: This function is 1:1 from `instructor.dsl.simple_type.is_simple_type`"""

    # Special case for Python 3.9: Directly handle list[Union[int, str]] pattern
    import sys

    if sys.version_info < (3, 10):
        # Check if it's a list type with Union arguments using string representation
        if str(t).startswith("list[typing.Union[") or "list[Union[" in str(t):
            return True

    try:
        if isclass(t) and _validateIsSubClass(t):
            return False
    except TypeError:
        # ! In versions < 3.11, typing.Iterable is not a class, so we can't use isclass
        # ! for now if `t` is an Iterable isclass and issubclass will raise
        # ! TypeError, so we need to check if `t` is an Iterable
        # ! This is a workaround for now, we should fix this in later PRs
        return False

    # Get the origin of the response model
    origin = typing.get_origin(t)

    # Handle special case for list[int | str], list[Union[int, str]] or similar type patterns
    # Identify a list type by checking for various origins it might have
    if origin in {typing.Iterable, list}:
        # For list types, check the contents before deciding
        if origin is list:
            # Extract the inner types from the list
            args = typing.get_args(t)
            if args and len(args) == 1:
                inner_arg = args[0]
                # Special handling for Union types
                inner_origin = typing.get_origin(inner_arg)

                # Explicit check for Union types - try different patterns across Python versions
                if (
                    inner_origin is typing.Union
                    or inner_origin == typing.Union
                    or str(inner_origin) == "typing.Union"
                    or str(type(inner_arg)) == "<class 'typing._UnionGenericAlias'>"
                ):
                    return True

                # Check for Python 3.10+ pipe syntax
                if hasattr(inner_arg, "__or__"):
                    return True

                # For simple list with basic types, also return True
                if inner_arg in {str, int, float, bool}:
                    return True

                # Check if inner type is a BaseModel - if so, not a simple type
                try:
                    if isclass(inner_arg) and issubclass(inner_arg, BaseModel):
                        return False
                except TypeError:
                    pass

            # If no args or unknown pattern, treat as simple list
            return len(args) == 0

        # Extract the inner types from the list for other iterable types
        args = typing.get_args(t)
        if args and len(args) == 1:
            inner_arg = args[0]
            # Special handling for Union types
            inner_origin = typing.get_origin(inner_arg)

            # Explicit check for Union types - try different patterns across Python versions
            if (
                inner_origin is typing.Union
                or inner_origin == typing.Union
                or str(inner_origin) == "typing.Union"
                or str(type(inner_arg)) == "<class 'typing._UnionGenericAlias'>"
            ):
                return True

            # Check for Python 3.10+ pipe syntax
            if hasattr(inner_arg, "__or__"):
                return True

            # For simple list with basic types, also return True
            if inner_arg in {str, int, float, bool}:
                return True

        # For other iterable patterns, return False (e.g., streaming types)
        return False

    if t in {
        str,
        int,
        float,
        bool,
    }:
        return True

    # If the t is a simple type like annotated
    if origin in {
        typing.Annotated,
        typing.Literal,
        typing.Union,
        list,  # origin of List[T] is list
    }:
        return True

    if isclass(t) and issubclass(t, Enum):
        return True

    return False


def get_type_description(t: typing.Any) -> str:
    """Creates a human-readable description of a type hint.

    Args:
        t : The type hint to create a description for.

    Returns:
        A human-readable description of the type hint.
    """
    origin = typing_inspect.get_origin(t)
    args = typing_inspect.get_args(t)

    if origin is None:
        # Handle basic types that should have special names
        if t is list:
            return "array"
        elif t is dict:
            return "object"
        elif t is tuple:
            return "tuple"
        elif hasattr(t, "__name__"):
            return t.__name__
        return str(t)

    if origin is list:
        if args:
            return f"array of {get_type_description(args[0])}"
        return "array"

    if origin is dict:
        if len(args) == 2:
            return f"object with {get_type_description(args[0])} keys and {get_type_description(args[1])} values"
        return "object"

    if origin is tuple:
        if args:
            arg_descriptions = [get_type_description(arg) for arg in args]
            return f"tuple of ({', '.join(arg_descriptions)})"
        return "tuple"

    if typing_inspect.is_literal_type(t):
        if args:
            values = [repr(arg) for arg in args]
            return f"one of: {', '.join(values)}"
        return "literal"

    # Handle Union types (including Optional)
    if typing_inspect.is_union_type(t):
        if typing_inspect.is_optional_type(t):
            # This is Optional[T]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                return f"optional {get_type_description(non_none_args[0])}"
        else:
            # This is Union[T1, T2, ...]
            arg_descriptions = [get_type_description(arg) for arg in args]
            return f"one of: {', '.join(arg_descriptions)}"

    # Handle callable types
    if typing_inspect.is_callable_type(t):
        if args and len(args) >= 2:
            param_types_arg = args[0]  # First arg is the parameter types
            return_type = args[1]  # Second arg is the return type

            # param_types_arg is either a list of types or ... (Ellipsis)
            if param_types_arg is ...:
                return f"function(...) -> {get_type_description(return_type)}"
            elif isinstance(param_types_arg, (list, tuple)):
                if param_types_arg:
                    param_descriptions = [
                        get_type_description(param) for param in param_types_arg
                    ]
                    return f"function({', '.join(param_descriptions)}) -> {get_type_description(return_type)}"
                else:
                    return f"function() -> {get_type_description(return_type)}"
        return "function"

    # Handle generic types
    if typing_inspect.is_generic_type(t):
        if args:
            arg_descriptions = [get_type_description(arg) for arg in args]
            return f"{origin.__name__}[{', '.join(arg_descriptions)}]"
        return str(origin)

    # Handle final types
    if typing_inspect.is_final_type(t):
        if args:
            return f"final {get_type_description(args[0])}"
        return "final"

    # Handle forward references
    if typing_inspect.is_forward_ref(t):
        return f"forward_ref({t.__forward_arg__})"

    # Handle new types
    if typing_inspect.is_new_type(t):
        return f"new_type({t.__name__})"

    # Handle type variables
    if typing_inspect.is_typevar(t):
        return f"typevar({t.__name__})"

    return str(t)


def get_standardized_type_name(t: typing.Any) -> str:
    """Creates a standardized name for a type hint.

    Args:
        t : The type hint to create a name for.

    Returns:
        A standardized name for the type hint.
    """
    origin = typing_inspect.get_origin(t)
    args = typing_inspect.get_args(t)

    if origin is None:
        # Handle basic types
        if t is list:
            return "Array"
        elif t is dict:
            return "Object"
        elif t is tuple:
            return "Tuple"
        elif hasattr(t, "__name__"):
            return t.__name__
        return str(t)

    if origin is list:
        if args:
            return f"ArrayOf{get_standardized_type_name(args[0])}"
        return "Array"

    if origin is dict:
        if len(args) == 2:
            return f"DictOf{get_standardized_type_name(args[0])}To{get_standardized_type_name(args[1])}"
        return "Dict"

    if origin is tuple:
        if args:
            arg_names = [get_standardized_type_name(arg) for arg in args]
            return f"TupleOf{'And'.join(arg_names)}"
        return "Tuple"

    # Handle Literal types - use "Options" instead
    if typing_inspect.is_literal_type(t):
        return "Options"

    # Handle Union types (including Optional) - use "Options" instead
    if typing_inspect.is_union_type(t):
        if typing_inspect.is_optional_type(t):
            # This is Optional[T]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                return f"Optional{get_standardized_type_name(non_none_args[0])}"
        else:
            # This is Union[T1, T2, ...] - use "Options"
            return "Options"

    # Handle callable types - return the function name if available
    if typing_inspect.is_callable_type(t):
        if hasattr(t, "__name__"):
            return t.__name__
        return "Callable"

    # Handle generic types
    if typing_inspect.is_generic_type(t):
        if args:
            arg_names = [get_standardized_type_name(arg) for arg in args]
            return f"{origin.__name__}Of{'And'.join(arg_names)}"
        if hasattr(origin, "__name__"):
            return origin.__name__
        return str(origin)

    # Handle final types
    if typing_inspect.is_final_type(t):
        if args:
            return get_standardized_type_name(args[0])
        return "Final"

    # Handle forward references
    if typing_inspect.is_forward_ref(t):
        return t.__forward_arg__

    # Handle new types
    if typing_inspect.is_new_type(t):
        return t.__name__

    # Handle type variables
    if typing_inspect.is_typevar(t):
        return t.__name__

    return str(t)


def get_literal_type_values(
    t: typing.Any,
) -> typing.List[str | int | float | bool | None]:
    """Extracts the values from a Literal type hint."""
    if typing_inspect.is_literal_type(t):
        return list(typing_inspect.get_args(t))
    return []


def is_value_in_literal_type(
    item: typing.Any, literal: typing.Type[typing.Any] | typing.Any
) -> bool:
    """Checks if a value is part of a Literal type hint."""
    if typing_inspect.is_literal_type(literal):
        return item in typing_inspect.get_args(literal)
    return False


def get_enum_type_values(
    t: typing.Type[Enum],
) -> typing.List[str | int | float | bool | None]:
    """Extracts the values/item from an Enum type."""
    if issubclass(t, Enum):
        return [member.value for member in t]
    return []


def is_key_in_enum_type(item: typing.Any, enum_type: typing.Type[Enum]) -> bool:
    """Checks if a value/item is part of an Enum type."""
    if issubclass(enum_type, Enum):
        return item in [member.name for member in enum_type]
    return False


def is_value_in_enum_type(item: typing.Any, enum_type: typing.Type[Enum]) -> bool:
    """Checks if a value is part of an Enum type."""
    if issubclass(enum_type, Enum):
        return item in [member.value for member in enum_type]
    return False
