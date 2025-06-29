"""hammad.cache

Contains helpful resources for creating simple cache systems, and
decorators that implement "automatic" hashing & caching of function calls.
"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .base_cache import BaseCache, CacheParams, CacheReturn, CacheType
    from .file_cache import FileCache
    from .ttl_cache import TTLCache
    from .cache import Cache, create_cache
    from .decorators import (
        cached,
        auto_cached,
        get_decorator_cache,
        clear_decorator_cache,
    )


__all__ = (
    # hammad.cache.base_cache
    "BaseCache",
    "CacheParams",
    "CacheReturn",
    "CacheType",
    # hammad.cache.file_cache
    "FileCache",
    # hammad.cache.ttl_cache
    "TTLCache",
    # hammad.cache.cache
    "Cache",
    "create_cache",
    # hammad.cache.decorators
    "cached",
    "auto_cached",
    "get_decorator_cache",
    "clear_decorator_cache",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
