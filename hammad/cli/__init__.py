"""hammad.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugins import print, input, animate


__all__ = (
    "print",
    "input",
    "animate",
)


_MODULE_CACHE = {}

def __getattr__(name: str):
    """Get an attribute from the plugins module."""
    if 'plugins' not in _MODULE_CACHE:
        _MODULE_CACHE['plugins'] = import_module(f".plugins", __package__)
    return getattr(_MODULE_CACHE['plugins'], name)

def __dir__() -> list[str]:
    """Get the attributes of the plugins module.""" 
    if 'plugins' not in _MODULE_CACHE:
        _MODULE_CACHE['plugins'] = import_module(f".plugins", __package__)
    return list(_MODULE_CACHE['plugins'].__all__)