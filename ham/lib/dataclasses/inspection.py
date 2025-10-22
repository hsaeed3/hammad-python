"""ham.lib.dataclasses.inspection"""

from dataclasses import (
    is_dataclass,
    fields,
)
from typing import TypeVar, Type


__all__ = (
    "get_dataclass_field_names",
    "get_dataclass_cls",
    "is_dataclass_instance",
    "is_dataclass",
)


Dataclass = TypeVar("Dataclass")


def get_dataclass_field_names(t: Dataclass | Type[Dataclass]) -> list[str]:
    """Returns a list of field names within a dataclass."""
    if not is_dataclass(t):
        raise TypeError("Provided object is not a dataclass.")
    return [field.name for field in fields(t)]


def get_dataclass_cls(t: Dataclass | Type[Dataclass]) -> Type[Dataclass]:
    """Returns the dataclass type for a dataclass instance."""
    if not is_dataclass(t):
        raise TypeError("Provided object is not a dataclass.")
    if isinstance(t, type):
        return t
    return type(t)


def is_dataclass_instance(t: Dataclass | Type[Dataclass]) -> bool:
    """Determines if the provided object is an instance of a dataclass."""
    return is_dataclass(t) and not isinstance(t, type)
