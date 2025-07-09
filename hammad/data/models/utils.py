"""hammad.data.models.utils"""

from functools import lru_cache
from typing import Any, Callable, Optional, Union, Tuple, Dict

from msgspec.structs import Struct

from .fields import FieldInfo, field, Field
from .model import Model


__all__ = (
    "create_model",
    "get_field_info",
    "is_field",
    "is_model",
    "validator",
)


def create_model(
    __model_name: str,
    *,
    __base__: Optional[Union[type, Tuple[type, ...]]] = None,
    __module__: Optional[str] = None,
    __qualname__: Optional[str] = None,
    __doc__: Optional[str] = None,
    __validators__: Optional[Dict[str, Any]] = None,
    __config__: Optional[type] = None,
    **field_definitions: Any,
) -> type[Model]:
    """Create a Model dynamically with Pydantic-compatible interface.

    This function provides a drop-in replacement for pydantic.create_model()
    that creates Model classes instead of pydantic BaseModel classes.

    Args:
        __model_name: Name of the model class to create
        __base__: Base class(es) to inherit from. If None, uses Model.
                  Can be a single class or tuple of classes.
        __module__: Module name for the created class
        __qualname__: Qualified name for the created class
        __doc__: Docstring for the created class
        __validators__: Dictionary of validators (for compatibility - not fully implemented)
        __config__: Configuration class (for compatibility - not fully implemented)
        **field_definitions: Field definitions as keyword arguments.
                           Each can be:
                           - A type annotation (e.g., str, int)
                           - A tuple of (type, default_value)
                           - A tuple of (type, Field(...))
                           - A Field instance

    Returns:
        A new Model class with the specified fields

    Examples:
        # Simple model with basic types
        User = create_model('User', name=str, age=int)

        # Model with defaults
        Config = create_model('Config',
                                  host=(str, 'localhost'),
                                  port=(int, 8080))

        # Model with field constraints
        Product = create_model('Product',
                                   name=str,
                                   price=(float, field(gt=0)),
                                   tags=(List[str], field(default_factory=list)))

        # Model with custom base class
        class BaseEntity(Model):
            id: int
            created_at: str

        User = create_model('User',
                                name=str,
                                email=str,
                                __base__=BaseEntity)
    """
    # Handle base class specification
    if __base__ is not None and __config__ is not None:
        raise ValueError(
            "Cannot specify both '__base__' and '__config__' - "
            "use a base class with the desired configuration instead"
        )

    # Determine base classes
    if __base__ is None:
        bases = (Model,)
    elif isinstance(__base__, tuple):
        # Ensure all bases are compatible
        for base in __base__:
            if not (issubclass(base, Model) or issubclass(base, Struct)):
                raise ValueError(
                    f"Base class {base} must be a subclass of Model or msgspec.Struct"
                )
        bases = __base__
    else:
        if not (issubclass(__base__, Model) or issubclass(__base__, Struct)):
            raise ValueError(
                f"Base class {__base__} must be a subclass of Model or msgspec.Struct"
            )
        bases = (__base__,)

    # Build class dictionary
    class_dict = {}
    annotations = {}

    # Set metadata
    if __doc__ is not None:
        class_dict["__doc__"] = __doc__
    if __module__ is not None:
        class_dict["__module__"] = __module__
    if __qualname__ is not None:
        class_dict["__qualname__"] = __qualname__

    # Process field definitions in two passes to ensure proper ordering
    # First pass: collect required and optional fields separately
    required_fields = {}
    optional_fields = {}

    for field_name, field_definition in field_definitions.items():
        if field_name.startswith("__") and field_name.endswith("__"):
            # Skip special attributes that were passed as field definitions
            continue

        # Parse field definition
        is_optional = False

        if isinstance(field_definition, tuple):
            if len(field_definition) == 2:
                field_type, field_value = field_definition
                annotations[field_name] = field_type

                # Check if field_value is a Field instance or field
                if hasattr(field_value, "__class__") and (
                    "field" in field_value.__class__.__name__.lower()
                    or hasattr(field_value, "default")
                    or callable(getattr(field_value, "__call__", None))
                ):
                    # It's a field descriptor
                    optional_fields[field_name] = field_value
                else:
                    # It's a default value - create a field with this default
                    optional_fields[field_name] = field(default=field_value)
                is_optional = True
            else:
                raise ValueError(
                    f"Field definition for '{field_name}' must be a 2-tuple of (type, default/Field)"
                )
        elif hasattr(field_definition, "__origin__") or hasattr(
            field_definition, "__class__"
        ):
            # It's a type annotation (like str, int, List[str], etc.) - required field
            annotations[field_name] = field_definition
            required_fields[field_name] = None
        else:
            # It's likely a default value without type annotation
            # We'll infer the type from the value
            annotations[field_name] = type(field_definition)
            optional_fields[field_name] = field(default=field_definition)
            is_optional = True

    # Second pass: add fields in correct order (required first, then optional)
    # This ensures msgspec field ordering requirements are met
    for field_name, field_value in required_fields.items():
        if field_value is not None:
            class_dict[field_name] = field_value

    for field_name, field_value in optional_fields.items():
        class_dict[field_name] = field_value

    # Set annotations in proper order (required fields first, then optional)
    ordered_annotations = {}

    # Add required field annotations first
    for field_name in required_fields:
        if field_name in annotations:
            ordered_annotations[field_name] = annotations[field_name]

    # Add optional field annotations second
    for field_name in optional_fields:
        if field_name in annotations:
            ordered_annotations[field_name] = annotations[field_name]

    class_dict["__annotations__"] = ordered_annotations

    # Handle validators (basic implementation for compatibility)
    if __validators__:
        # Store validators for potential future use
        class_dict["_validators"] = __validators__
        # Note: Full validator implementation would require more complex integration

    # Create the dynamic class
    try:
        DynamicModel = type(__model_name, bases, class_dict)
    except Exception as e:
        raise ValueError(f"Failed to create model '{__model_name}': {e}") from e

    return DynamicModel


@lru_cache(maxsize=None)
def get_field_info(field: Any) -> Optional[FieldInfo]:
    """Extract FieldInfo from a field descriptor with caching."""
    if isinstance(field, tuple) and len(field) == 2:
        _, field_info = field
        if isinstance(field_info, FieldInfo):
            return field_info
    elif hasattr(field, "_field_info"):
        return field._field_info
    elif hasattr(field, "field_info"):
        return field.field_info
    elif isinstance(field, Field):
        return field.field_info
    elif hasattr(field, "__class__") and field.__class__.__name__ == "FieldDescriptor":
        return field.field_info
    return None


def is_field(field: Any) -> bool:
    """Check if a field is a field."""
    return get_field_info(field) is not None


def is_model(model: Any) -> bool:
    """Check if a model is a model."""
    # Check if it's an instance of Model
    if isinstance(model, Model):
        return True

    # Check if it's a Model class (not instance)
    if isinstance(model, type) and issubclass(model, Model):
        return True

    # Check for Model characteristics using duck typing
    # Look for key Model/msgspec.Struct attributes and methods
    if hasattr(model, "__struct_fields__") and hasattr(model, "model_dump"):
        # Check for Model-specific methods
        if (
            hasattr(model, "model_copy")
            and hasattr(model, "model_validate")
            and hasattr(model, "model_to_pydantic")
        ):
            return True

    # Check if it's an instance of any msgspec Struct with Model methods
    try:
        if isinstance(model, Struct) and hasattr(model, "model_dump"):
            return True
    except ImportError:
        pass

    return False


def validator(
    *fields: str, pre: bool = False, post: bool = False, always: bool = False
):
    """Decorator to create a validator for specific fields.

    Args:
        *fields: Field names to validate
        pre: Whether this is a pre-validator
        post: Whether this is a post-validator
        always: Whether to run even if the value is not set

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func._validator_fields = fields
        func._validator_pre = pre
        func._validator_post = post
        func._validator_always = always
        return func

    return decorator
