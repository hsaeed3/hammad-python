"""hammad.pydantic

Contains both models and pydantic **specific** utiltiies / resources
meant for general case usage."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .converters import (
        convert_to_pydantic_model,
        convert_to_pydantic_field,
        create_confirmation_pydantic_model,
        create_selection_pydantic_model,
    )


__all__ = (
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "create_confirmation_pydantic_model",
    "create_selection_pydantic_model",
)


def __getattr__(name: str):
    """Get an attribute from the pydantic module."""
    from importlib import import_module

    if not hasattr(__getattr__, "_pydantic_module"):
        __getattr__._pydantic_module = import_module(f".converters", __package__)
    return getattr(__getattr__._pydantic_module, name)


def __dir__() -> list[str]:
    """Get the attributes of the pydantic module."""
    return list(__all__)
