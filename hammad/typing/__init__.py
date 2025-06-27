"""hammad.utils.typing

Contains various utility functions in regards to typing or working
with type hints. These utils are also exposed in:

```python
import hammad

hammad.typing.get_type_description(Optional[int])
...
```
"""

from typing import Any, TYPE_CHECKING
import typing_inspect as inspection
from typing_inspect import (
    is_callable_type,
    is_classvar,
    is_final_type,
    is_forward_ref,
    is_generic_type,
    is_literal_type,
    is_new_type,
    is_optional_type,
    is_union_type,
    is_typevar,
    is_tuple_type,
    get_origin,
    get_args,
    get_last_args,
    get_last_origin,
    get_generic_bases,
    typed_dict_keys as get_typed_dict_keys,
)
from typing_inspection.introspection import (
    is_union_origin,
    inspect_annotation,
    get_literal_values,
)
from dataclasses import is_dataclass

__all__ = (
    "TypingError",
    "get_type_description",
    "inspection",
    "is_pydantic_basemodel",
    "is_pydantic_basemodel_instance",
    "is_msgspec_struct",
    "is_dataclass",
    "is_callable_type",
    "is_classvar",
    "is_final_type",
    "is_forward_ref",
    "is_generic_type",
    "is_literal_type",
    "is_new_type",
    "is_optional_type",
    "is_union_type",
    "is_typevar",
    "is_tuple_type",
    "get_origin",
    "get_args",
    "is_union_origin",
    "inspect_annotation",
    "get_literal_values",
    "get_last_args",
    "get_last_origin",
    "get_generic_bases",
    "get_typed_dict_keys",
)


class TypingError(Exception):
    """An exception raised when a type utility raises an error."""


# ------------------------------------------------------------------------
# Inspection Extensions
# ------------------------------------------------------------------------


def is_pydantic_basemodel(t: Any) -> bool:
    """Check if an object is a Pydantic BaseModel class or instance using duck typing.

    This function uses duck typing to identify Pydantic BaseModel objects by checking
    for the presence of characteristic attributes (`model_fields` and `model_dump`)
    without requiring direct imports of Pydantic.

    Args:
        t: The object to check. Can be a class, instance, or any other type.

    Returns:
        True if the object appears to be a Pydantic BaseModel (class or instance),
        False otherwise.

    Example:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> is_pydantic_basemodel(User)
        True
        >>> is_pydantic_basemodel(User(name="John"))
        True
        >>> is_pydantic_basemodel(dict)
        False
    """
    # Check if it's a class first
    if isinstance(t, type):
        return (
            hasattr(t, "model_fields")
            and hasattr(t, "model_dump")
            and callable(getattr(t, "model_dump", None))
        )

    # For instances, check the class instead of the instance to avoid deprecation warning
    return (
        hasattr(t.__class__, "model_fields")
        and hasattr(t, "model_dump")
        and callable(getattr(t, "model_dump", None))
    )


def is_pydantic_basemodel_instance(t: Any) -> bool:
    """Check if an object is an instance (not class) of a Pydantic BaseModel using duck typing.

    This function specifically identifies Pydantic BaseModel instances by ensuring
    the object is not a type/class itself and has the characteristic Pydantic attributes.

    Args:
        t: The object to check.

    Returns:
        True if the object is a Pydantic BaseModel instance (not the class itself),
        False otherwise.

    Example:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> user = User(name="John")
        >>> is_pydantic_basemodel_instance(user)
        True
        >>> is_pydantic_basemodel_instance(User)  # Class, not instance
        False
    """
    return (
        not isinstance(t, type)
        and hasattr(t.__class__, "model_fields")
        and hasattr(t, "model_dump")
        and callable(getattr(t, "model_dump", None))
    )


def is_msgspec_struct(t: Any) -> bool:
    """Check if an object is a msgspec Struct class or instance using duck typing.

    This function uses duck typing to identify msgspec Struct objects by checking
    for the presence of characteristic attributes (`__struct_fields__` and
    `__struct_config__`) without requiring direct imports of msgspec.

    Args:
        t: The object to check. Can be a class, instance, or any other type.

    Returns:
        True if the object appears to be a msgspec Struct (class or instance),
        False otherwise.

    Example:
        >>> import msgspec
        >>> class User(msgspec.Struct):
        ...     name: str
        >>> is_msgspec_struct(User)
        True
        >>> is_msgspec_struct(User(name="John"))
        True
        >>> is_msgspec_struct(dict)
        False
    """
    return hasattr(t, "__struct_fields__") and hasattr(t, "__struct_config__")


def get_type_description(t: Any) -> str:
    """Creates a human-readable description of a type hint.

    Args:
        t : The type hint to create a description for.

    Returns:
        A human-readable description of the type hint.
    """
    origin = inspection.get_origin(t)
    args = inspection.get_args(t)

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

    if inspection.is_literal_type(t):
        if args:
            values = [repr(arg) for arg in args]
            return f"one of: {', '.join(values)}"
        return "literal"

    # Handle Union types (including Optional)
    if inspection.is_union_type(t):
        if inspection.is_optional_type(t):
            # This is Optional[T]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                return f"optional {get_type_description(non_none_args[0])}"
        else:
            # This is Union[T1, T2, ...]
            arg_descriptions = [get_type_description(arg) for arg in args]
            return f"one of: {', '.join(arg_descriptions)}"

    # Handle callable types
    if inspection.is_callable_type(t):
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
    if inspection.is_generic_type(t):
        if args:
            arg_descriptions = [get_type_description(arg) for arg in args]
            return f"{origin.__name__}[{', '.join(arg_descriptions)}]"
        return str(origin)

    # Handle final types
    if inspection.is_final_type(t):
        if args:
            return f"final {get_type_description(args[0])}"
        return "final"

    # Handle forward references
    if inspection.is_forward_ref(t):
        return f"forward_ref({t.__forward_arg__})"

    # Handle new types
    if inspection.is_new_type(t):
        return f"new_type({t.__name__})"

    # Handle type variables
    if inspection.is_typevar(t):
        return f"typevar({t.__name__})"

    return str(t)


if TYPE_CHECKING:
    pass


def create_lazy_loader(imports_dict: dict[str, str], package: str):
    """Create a lazy loader function for __getattr__.

    Args:
        imports_dict: Dictionary mapping attribute names to their module paths
        package: The package name for import_module

    Returns:
        A __getattr__ function that lazily imports modules
    """

    def __getattr__(name: str):
        if name in imports_dict:
            from importlib import import_module

            module = import_module(imports_dict[name], package)
            return getattr(module, name)
        raise AttributeError(f"module '{package}' has no attribute '{name}'")

    return __getattr__


def parse_type_checking_imports(source_code: str) -> dict[str, str]:
    """Parse TYPE_CHECKING imports from source code to build import map.

    This is a simple parser that extracts import information from
    TYPE_CHECKING blocks to automatically build the module map.

    Args:
        source_code: The source code containing TYPE_CHECKING imports

    Returns:
        Dictionary mapping imported names to their module paths
    """
    import ast
    import re

    # Parse the source code
    tree = ast.parse(source_code)

    imports_map = {}
    in_type_checking = False

    for node in ast.walk(tree):
        # Check if we're in a TYPE_CHECKING block
        if isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
            ) or (
                isinstance(node.test, ast.Attribute)
                and isinstance(node.test.value, ast.Name)
                and node.test.value.id == "typing"
                and node.test.attr == "TYPE_CHECKING"
            ):
                # Process imports in the TYPE_CHECKING block
                for stmt in node.body:
                    if isinstance(stmt, ast.ImportFrom):
                        module = stmt.module or ""
                        for alias in stmt.names:
                            name = alias.asname or alias.name
                            imports_map[name] = f".{module}"

    return imports_map
