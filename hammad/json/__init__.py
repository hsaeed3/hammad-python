"""hammad.utils.json"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .converters import convert_to_json_schema

__all__ = ("convert_to_json_schema",)


def __getattr__(name: str):
    """Get an attribute from the json module."""
    from importlib import import_module

    if not hasattr(__getattr__, "_json_module"):
        __getattr__._json_module = import_module(f".converters", __package__)
    return getattr(__getattr__._json_module, name)


def __dir__() -> list[str]:
    """Get the attributes of the json module."""
    return list(__all__)
