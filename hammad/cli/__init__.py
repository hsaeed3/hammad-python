"""hammad.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugins import print, input, animate


__all__ = (
    "print",
    "input",
    "animate",
)


def __getattr__(name: str):
    """Get an attribute from the plugins module."""
    from importlib import import_module

    if not hasattr(__getattr__, "_plugins_module"):
        __getattr__._plugins_module = import_module(f".plugins", __package__)
    return getattr(__getattr__._plugins_module, name)


def __dir__() -> list[str]:
    """Get the attributes of the plugins module."""
    from importlib import import_module

    if not hasattr(__dir__, "_plugins_module"):
        __dir__._plugins_module = import_module(f".plugins", __package__)
    return list(__dir__._plugins_module.__all__)
