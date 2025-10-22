"""ham.inspection.dataclasses"""

from dataclasses import (
    is_dataclass,
    fields,
)
from typing import TypeVar


__all__ = (
    "get_dataclass_field_names",
    "get_dataclass_type",
    "is_dataclass_instance",
    "is_dataclass",
)


_D = TypeVar("_D")


def get_dataclass_field_names(t: object) -> list[str]:
    """Returns a list of field names within a dataclass."""
    if not is_dataclass(t):
        raise TypeError("Provided object is not a dataclass.")
    return [field.name for field in fields(t)]


def get_dataclass_type(t: _D) -> TypeVar["_D"]:
    """Returns the dataclass type for a dataclass instance."""
    if not is_dataclass(t):
        raise TypeError("Provided object is not a dataclass.")
    if isinstance(t, type):
        return t
    return type(t)


def is_dataclass_instance(t: object) -> bool:
    """Determines if the provided object is an instance of a dataclass."""
    return is_dataclass(t) and not isinstance(t, type)
