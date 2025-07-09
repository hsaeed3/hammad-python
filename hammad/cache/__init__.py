"""hammad.cache"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer


if TYPE_CHECKING:
    from .base_cache import BaseCache, CacheParams, CacheReturn, CacheType
    from .file_cache import FileCache, FileCacheLocation
    from .ttl_cache import TTLCache
    from .cache import Cache, create_cache
    from .decorators import cached, auto_cached, clear_decorator_cache


__all__ = (
    # hammad.performance.cache.base_cache
    "BaseCache",
    "CacheParams",
    "CacheReturn",
    "CacheType",
    # hammad.performance.cache.file_cache
    "FileCache",
    "FileCacheLocation",
    # hammad.performance.cache.ttl_cache
    "TTLCache",
    # hammad.performance.cache.cache
    "Cache",
    "create_cache",
    # hammad.performance.cache.decorators
    "cached",
    "auto_cached",
    "clear_decorator_cache",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return sorted(__all__)
