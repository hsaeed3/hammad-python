"""hammad.data.models.extensions.pydantic.converters

Contains various converters for converting various objects into
a Pydantic model. These converters are used to convert
various objects into a Pydantic model, such as types,
docstrings, and other objects."""

import inspect
import logging
from dataclasses import is_dataclass, fields as dataclass_fields, MISSING
from docstring_parser import parse
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    Type,
    Union,
    Mapping,
    get_type_hints,
    Callable,
    Sequence,
    TypeVar,
    Tuple,
    List,
    overload,
    cast,
)
from pydantic import BaseModel, Field, create_model

from typing import get_origin, get_args
from typing_inspect import is_generic_type

logger = logging.getLogger(__name__)

__all__ = [
    "is_pydantic_model_class",
    "get_pydantic_fields_from_function",
    "convert_to_pydantic_field",
    "convert_to_pydantic_model",
    "create_selection_pydantic_model",
    "create_confirmation_pydantic_model",
    "convert_dataclass_to_pydantic_model",
    "convert_type_to_pydantic_model",
    "convert_function_to_pydantic_model",
    "convert_sequence_to_pydantic_model",
    "convert_dict_to_pydantic_model",
]


# -----------------------------------------------------------------------------
# Types & Constants
# -----------------------------------------------------------------------------

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
"""Helper type for Pydantic model classes."""


JSON_TYPE_MAPPING: Mapping[Any, Tuple[str, Any]] = {
    int: ("int", int),
    float: ("float", float),
    bool: ("bool", bool),
    str: ("str", str),
    bytes: ("bytes", bytes),
    list: ("list", list),
    tuple: ("tuple", tuple),
    dict: ("dict", dict),
    set: ("set", set),
    frozenset: ("frozenset", frozenset),
    Any: ("any", Any),
    None: ("none", None),
    Union: ("union", Union),
    Optional: ("optional", Optional),
}
"""
A mapping of types to their string representations. Used for hinting & JSON schema
generation.
"""

TYPE_NAME_MAPPING: Dict[Type, str] = {
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    str: "String",
    bytes: "Bytes",
    list: "List",
    tuple: "Tuple",
    dict: "Dict",
    set: "Set",
    frozenset: "FrozenSet",
}
"""
A mapping of basic types to their semantic model names.
"""

FIELD_NAME_MAPPING: Dict[Type, str] = {
    int: "value",
    float: "value",
    bool: "flag",
    str: "text",
    bytes: "data",
    list: "items",
    tuple: "values",
    dict: "mapping",
    set: "elements",
    frozenset: "elements",
}
"""
A mapping of basic types to their semantic field names.
"""


# -----------------------------------------------------------------------------
# Pydantic Model Utils
# -----------------------------------------------------------------------------


def is_pydantic_model_class(obj: Any) -> bool:
    """
    Checks if an object is a Pydantic model class.
    """
    return isinstance(obj, type) and issubclass(obj, BaseModel)


def generate_semantic_model_name(type_hint: Type) -> str:
    """
    Generates a semantic model name based on the type.

    Examples:
        int -> "Integer"
        str -> "String"
        List[int] -> "IntegerList"
        Dict[str, int] -> "StringIntegerDict"
        Optional[int] -> "OptionalInteger"
        Union[str, int] -> "StringIntegerUnion"
    """
    # Handle basic types
    if type_hint in TYPE_NAME_MAPPING:
        return TYPE_NAME_MAPPING[type_hint]

    # Handle Optional types
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is Union:
        # Check if it's Optional (Union with None)
        if type(None) in args and len(args) == 2:
            # This is Optional[T]
            inner_type = next(arg for arg in args if arg is not type(None))
            return f"Optional{generate_semantic_model_name(inner_type)}"
        else:
            # Regular Union
            type_names = [
                generate_semantic_model_name(arg)
                for arg in args
                if arg is not type(None)
            ]
            return "".join(type_names) + "Union"

    # Handle generic types
    if origin is not None:
        origin_name = TYPE_NAME_MAPPING.get(origin, origin.__name__.capitalize())

        if args:
            # Generate names for type arguments
            arg_names = [generate_semantic_model_name(arg) for arg in args]
            if origin in (list, set, frozenset):
                # For collections, append the element type
                return f"{arg_names[0]}{origin_name}"
            elif origin is dict:
                # For dict, include both key and value types
                return f"{arg_names[0]}{arg_names[1]}Dict"
            elif origin is tuple:
                # For tuple, join all types
                return "".join(arg_names) + "Tuple"
            else:
                # For other generics, prepend type arguments
                return "".join(arg_names) + origin_name

        return origin_name

    # Fallback to the type's name
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__.capitalize()

    return "GeneratedModel"


def generate_semantic_field_name(type_hint: Type) -> str:
    """
    Generates a semantic field name based on the type.

    Examples:
        int -> "value"
        str -> "text"
        List[int] -> "items"
        Dict[str, int] -> "mapping"
        Optional[str] -> "text"
    """
    # Handle basic types
    if type_hint in FIELD_NAME_MAPPING:
        return FIELD_NAME_MAPPING[type_hint]

    # Handle Optional types - use the inner type's field name
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is Union:
        # Check if it's Optional (Union with None)
        if type(None) in args and len(args) == 2:
            # This is Optional[T] - use inner type's field name
            inner_type = next(arg for arg in args if arg is not type(None))
            return generate_semantic_field_name(inner_type)

    # Handle generic types - use the origin's field name
    if origin is not None and origin in FIELD_NAME_MAPPING:
        return FIELD_NAME_MAPPING[origin]

    # Default fallback
    return "value"


def get_pydantic_fields_from_function(func: Callable) -> Dict[str, Tuple[Type, Field]]:
    """
    Extracts Pydantic fields from a function's signature and docstring.
    Returns a dictionary mapping field names to (type, Pydantic Field) tuples.

    Args:
        func: The function to extract Pydantic fields from.

    Returns:
        A dictionary mapping field names to (type, Pydantic Field) tuples.
    """
    try:
        hints = get_type_hints(func)
        fields_dict: Dict[str, Tuple[Type, Field]] = {}
        doc_info = parse(func.__doc__ or "")

        for param_name, param_type in hints.items():
            if param_name == "return":
                continue

            description = ""
            if doc_info.params:
                description = (
                    next(
                        (
                            p.description
                            for p in doc_info.params
                            if p.arg_name == param_name
                        ),
                        "",
                    )
                    or ""
                )

            default_value = ...
            param = inspect.signature(func).parameters.get(param_name)
            if param and param.default is not inspect.Parameter.empty:
                default_value = param.default

            fields_dict[param_name] = (
                param_type,
                Field(default=default_value, description=description),
            )
        return fields_dict
    except Exception as e:
        logger.error(
            f"Error extracting function fields for {getattr(func, '__name__', 'unknown function')}: {e}"
        )
        return {}


def convert_to_pydantic_field(
    type_hint: Type,
    index: Optional[int] = None,
    description: Optional[str] = None,
    default: Any = ...,
) -> Dict[str, Tuple[Type, Field]]:
    """
    Creates a Pydantic field definition from a type hint.
    Returns a dictionary mapping a generated field name to its (type, Field) tuple.
    """
    try:
        # Use semantic field name if no index is provided
        if index is None:
            field_name = generate_semantic_field_name(type_hint)
        else:
            # Use indexed field name for sequences
            base_name = generate_semantic_field_name(type_hint)
            field_name = f"{base_name}_{index}"

        return {
            field_name: (
                type_hint,
                Field(default=default, description=description or ""),
            )
        }
    except Exception as e:
        logger.error(f"Error creating Pydantic field mapping for type {type_hint}: {e}")
        raise


# -----------------------------------------------------------------------------
# Simplified Model Creation
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Helpers (Private)
# -----------------------------------------------------------------------------


def convert_dataclass_to_pydantic_model(
    target: Union[Type, Any],  # NOTE: DATACLASS TYPE OR INSTANCE
    init: bool,
    name: Optional[str],
    description: Optional[str],
) -> Union[Type[BaseModel], BaseModel]:
    # Determine if we're dealing with a type or instance
    is_instance = not isinstance(target, type)
    dataclass_type = type(target) if is_instance else target

    model_name = name or dataclass_type.__name__
    doc_info = parse(dataclass_type.__doc__ or "")
    model_doc = description or doc_info.short_description

    pydantic_fields: Dict[str, Tuple[Type, Field]] = {}
    for dc_field in dataclass_fields(dataclass_type):
        field_type = dc_field.type
        field_default = dc_field.default if dc_field.default is not MISSING else ...  # type: ignore
        if dc_field.default_factory is not MISSING:  # type: ignore
            field_default = Field(default_factory=dc_field.default_factory)

        field_description = ""
        if doc_info.params:
            field_description = (
                next(
                    (
                        p.description
                        for p in doc_info.params
                        if p.arg_name == dc_field.name
                    ),
                    "",
                )
                or ""
            )

        pydantic_fields[dc_field.name] = (
            field_type,
            Field(default=field_default, description=field_description),
        )

    model_class = create_model(model_name, __doc__=model_doc, **pydantic_fields)

    if init and is_instance:
        instance_data = {
            f.name: getattr(target, f.name) for f in dataclass_fields(dataclass_type)
        }
        return model_class(**instance_data)
    return model_class


def convert_type_to_pydantic_model(
    target: Type,
    name: Optional[str],
    description: Optional[str],
    field_name: Optional[str],
    default: Any,
) -> Type[BaseModel]:
    # Use semantic naming if no name is provided
    model_name = name or generate_semantic_model_name(target)

    field_mapping = convert_to_pydantic_field(
        target, description=description, default=default
    )

    if field_name:  # Override default field name if explicitly provided
        current_field_def = list(field_mapping.values())[0]
        field_mapping = {field_name: current_field_def}

    return create_model(model_name, __doc__=(description or ""), **field_mapping)


def convert_function_to_pydantic_model(
    target: Callable,
    name: Optional[str],
    description: Optional[str],
) -> Type[BaseModel]:
    model_name = name or target.__name__
    doc_info = parse(target.__doc__ or "")
    model_doc = description or doc_info.short_description

    fields = get_pydantic_fields_from_function(target)
    return create_model(model_name, __doc__=model_doc, **fields)


def convert_sequence_to_pydantic_model(
    target: Sequence[Type],
    name: Optional[str],
    description: Optional[str],
    field_name: Optional[str],
    default: Any,
) -> Type[BaseModel]:
    if not target:
        raise ValueError("Cannot create Pydantic model from empty sequence")

    model_name = name or "GeneratedModel"
    pydantic_fields: Dict[str, Tuple[Type, Field]] = {}

    for i, type_hint in enumerate(target):
        if not isinstance(type_hint, type):
            raise ValueError(
                f"Sequence elements must be types, got {type_hint} at index {i}"
            )

        field_desc = description if i == 0 and field_name else None
        field_def_default = default if i == 0 and field_name else ...

        # Use provided field_name for the first element if specified
        current_field_name_override = field_name if i == 0 else None

        # Generate field(s) from type_hint
        temp_field_def = convert_to_pydantic_field(
            type_hint,
            index=None if current_field_name_override else i,
            description=field_desc,
            default=field_def_default,
        )

        actual_field_name = list(temp_field_def.keys())[0]
        actual_type_info = list(temp_field_def.values())[0]

        if current_field_name_override:
            pydantic_fields[current_field_name_override] = actual_type_info
        else:
            pydantic_fields[actual_field_name] = actual_type_info

    return create_model(model_name, __doc__=(description or ""), **pydantic_fields)


def convert_dict_to_pydantic_model(
    target: Dict[str, Any],
    init: bool,
    name: Optional[str],
    description: Optional[str],
) -> Union[Type[BaseModel], BaseModel]:
    model_name = name or "GeneratedModel"

    pydantic_fields: Dict[str, Tuple[Type, Field]] = {}
    for k, v in target.items():
        pydantic_fields[k] = (type(v), Field(default=v if init else ...))

    model_class = create_model(
        model_name, __doc__=(description or ""), **pydantic_fields
    )

    if init:
        return model_class(**target)
    return model_class


def _reconvert_to_pydantic_model_from_basemodel_instance(
    target: BaseModel,
    name: Optional[str],
    description: Optional[str],
) -> BaseModel:
    model_name = name or target.__class__.__name__
    doc_info = parse(target.__class__.__doc__ or "")
    model_doc = description or doc_info.short_description

    instance_data = target.model_dump()
    pydantic_fields: Dict[str, Tuple[Type, Field]] = {}
    for k, v_instance in instance_data.items():
        original_field_info = target.__class__.model_fields.get(k)
        field_desc = original_field_info.description if original_field_info else ""
        pydantic_fields[k] = (
            type(v_instance),
            Field(default=v_instance, description=field_desc),
        )

    new_model_class = create_model(model_name, __doc__=model_doc, **pydantic_fields)
    return new_model_class(**instance_data)


# ITS OVER 9000


@overload
def convert_to_pydantic_model(
    target: Type[BaseModelType],
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModelType]: ...
@overload
def convert_to_pydantic_model(
    target: Type[BaseModelType],
    init: Literal[True],
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> BaseModelType: ...
@overload
def convert_to_pydantic_model(
    target: BaseModelType,
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModelType]: ...
@overload
def convert_to_pydantic_model(
    target: BaseModelType,
    init: Literal[True],
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> BaseModelType: ...
@overload
def convert_to_pydantic_model(
    target: Type,
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModel]: ...
@overload
def convert_to_pydantic_model(
    target: Type,
    init: Literal[True],
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> BaseModel:  # For dataclass instances from type
    ...
@overload
def convert_to_pydantic_model(
    target: Callable,
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModel]: ...
@overload
def convert_to_pydantic_model(
    target: Sequence[Type],
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModel]: ...
@overload
def convert_to_pydantic_model(
    target: Dict[str, Any],
    init: Literal[False] = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Type[BaseModel]: ...
@overload
def convert_to_pydantic_model(
    target: Dict[str, Any],
    init: Literal[True],
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> BaseModel: ...


def convert_to_pydantic_model(
    target: Union[Type, Sequence[Type], Dict[str, Any], BaseModel, Callable],
    init: bool = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_name: Optional[str] = None,
    default: Any = ...,
) -> Union[Type[BaseModel], BaseModel]:
    """
    Converts various input types into a Pydantic model class or instance.

    Args:
        target: The target to convert (Python type, Pydantic BaseModel class/instance,
                dataclass type/instance, function, sequence of types, or dict).
        init: If True, returns an initialized Pydantic model instance where applicable
              (e.g., from a dict, dataclass instance, or BaseModel instance).
              If False (default), returns a Pydantic model class.
        name: Optional name for the generated Pydantic model.
        description: Optional description for the model (used as its docstring).
        field_name: Optional name for the primary field if `target` is a single type
                    or for the first field if `target` is a sequence of types.
        default: Optional default value if `target` is a single type, used with `field_name`.

    Returns:
        A Pydantic model class, or an instance of one if `init` is True and applicable.
    """
    # Handle existing Pydantic model classes
    if is_pydantic_model_class(target):
        target_cls = cast(Type[BaseModel], target)
        if init:
            try:
                return target_cls()
            except Exception as e:
                logger.warning(
                    f"Cannot auto-initialize {target_cls.__name__} due to missing required fields: {e}"
                )
                # Cannot create instance without required fields, return the class instead
                return target_cls
        if name and name != target_cls.__name__ or description:
            return _reconvert_to_pydantic_model_from_basemodel_instance(
                target_cls(), name=name, description=description
            )
        return target_cls

    # Handle Pydantic model instances
    if isinstance(target, BaseModel):
        if init:
            return _reconvert_to_pydantic_model_from_basemodel_instance(
                target, name=name, description=description
            )
        return target.__class__

    # Handle dataclasses (types or instances)
    if is_dataclass(target):
        if isinstance(target, type):
            # target is a dataclass type
            return convert_dataclass_to_pydantic_model(
                cast(Type, target),
                init=init,
                name=name,
                description=description,
            )
        else:
            # target is a dataclass instance
            return convert_dataclass_to_pydantic_model(
                target,  # Pass the instance directly
                init=init,
                name=name,
                description=description,
            )

    # Handle generic types (like list[str], dict[str, int], etc.)
    if is_generic_type(target) or get_origin(target) is not None:
        return convert_type_to_pydantic_model(
            target, name, description, field_name, default
        )

    # Handle standard Python types (int, str, etc.)
    if isinstance(target, type):
        return convert_type_to_pydantic_model(
            target, name, description, field_name, default
        )

    # Handle callables (functions)
    if callable(target):
        return convert_function_to_pydantic_model(target, name, description)

    # Handle sequences of types
    if isinstance(target, Sequence) and not isinstance(target, str):
        if not all(isinstance(t, type) for t in target):
            raise TypeError("If target is a sequence, all its elements must be types.")
        return convert_sequence_to_pydantic_model(
            cast(Sequence[Type], target), name, description, field_name, default
        )

    # Handle dictionaries
    if isinstance(target, dict):
        return convert_dict_to_pydantic_model(target, init, name, description)

    else:
        logger.error(
            f"Unsupported target type for Pydantic model creation: {type(target)} | how did you get here?"
        )
        raise TypeError(
            f"Cannot create Pydantic model from target of type {type(target)}"
        )


# -----------------------------------------------------------------------------
# Specialized Model Creation Utils
# -----------------------------------------------------------------------------


def create_selection_pydantic_model(
    fields: List[str],
    name: str = "Selection",
    description: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Creates a Pydantic model for making a selection from a list of string options.
    The model will have a single field named `selection` of type `Literal[*fields]`.

    Args:
        fields: A list of strings representing the allowed choices. Must not be empty.
        name: The name for the created Pydantic model.
        description: Optional description for the model (becomes its docstring).

    Returns:
        A new Pydantic BaseModel class with a 'selection' field.
    Raises:
        ValueError: If `fields` is empty.
    """
    if not fields:
        raise ValueError(
            "`fields` list cannot be empty for `create_selection_pydantic_model`."
        )

    literal_args_str = ", ".join(repr(str(f)) for f in fields)
    selection_type = eval(f"Literal[{literal_args_str}]")

    model_fields_definitions = {
        "selection": (
            selection_type,
            Field(..., description="The selected value from the available options."),
        )
    }
    model_docstring = (
        description or f"A model for selecting one option from: {', '.join(fields)}."
    )
    return create_model(
        name, __base__=BaseModel, __doc__=model_docstring, **model_fields_definitions
    )


def create_confirmation_pydantic_model(
    name: str = "Confirmation",
    description: Optional[str] = None,
    field_name: str = "confirmed",
) -> Type[BaseModel]:
    """
    Creates a Pydantic model for a boolean confirmation.
    The model will have a single boolean field.

    Args:
        name: The name for the created Pydantic model.
        description: Optional description for the model.
        field_name: Name of the boolean field in the model.

    Returns:
        A new Pydantic BaseModel class.
    """
    model_fields_definitions = {
        field_name: (bool, Field(..., description="The boolean confirmation value."))
    }
    model_docstring = description or "A model for boolean confirmation."
    return create_model(
        name, __base__=BaseModel, __doc__=model_docstring, **model_fields_definitions
    )
