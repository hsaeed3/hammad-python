"""hammad.cache"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._cache import auto_cached, cached, create_cache


__all__ = (
    "auto_cached",
    "cached",
    "create_cache",
)


def __getattr__(name: str):
    """Get an attribute from the cache module."""
    from importlib import import_module

    if not hasattr(__getattr__, "_cache_module"):
        __getattr__._cache_module = import_module(f"._cache", __package__)
    return getattr(__getattr__._cache_module, name)


def __dir__() -> list[str]:
    """Get the attributes of the cache module."""
    from importlib import import_module

    if not hasattr(__dir__, "_cache_module"):
        __dir__._cache_module = import_module(f"._cache", __package__)
    return list(__dir__._cache_module.__all__)
