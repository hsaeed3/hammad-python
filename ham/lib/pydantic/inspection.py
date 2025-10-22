"""ham.lib.pydantic.inspection

Contains introspection utilities in relation to Pydantic models and
types."""

from typing import TypeVar

__all__ = (
    "is_pydantic_basemodel",
    "is_pydantic_basemodel_instance",
    "get_pydantic_model_field_names",
    "get_pydantic_model_cls",
)


BaseModel = TypeVar("BaseModel")


def is_pydantic_basemodel(t: BaseModel) -> bool:
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


def is_pydantic_basemodel_instance(t: BaseModel) -> bool:
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


def get_pydantic_model_field_names(model: BaseModel) -> list[str]:
    """Returns a list of field names for a Pydantic BaseModel class or instance.

    Args:
        model: The Pydantic BaseModel class or instance.

    Returns:
        A list of field names defined in the Pydantic model.

    Raises:
        TypeError: If the provided object is not a Pydantic BaseModel class or instance
    """
    if not is_pydantic_basemodel(model):
        raise TypeError(
            "Provided object is not a Pydantic BaseModel class or instance."
        )

    # Access the model_fields attribute from the class
    model_class = model if isinstance(model, type) else model.__class__
    return list(model_class.model_fields.keys())


def get_pydantic_model_cls(model: BaseModel) -> type[BaseModel]:
    """Returns the Pydantic BaseModel type for a Pydantic model instance.

    Args:
        model: The Pydantic BaseModel instance.

    Returns:
        The Pydantic BaseModel class/type of the instance.

    Raises:
        TypeError: If the provided object is not a Pydantic BaseModel instance
    """
    if not is_pydantic_basemodel_instance(model):
        raise TypeError("Provided object is not a Pydantic BaseModel instance.")

    return model.__class__
