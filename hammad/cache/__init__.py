"""hammad.cache"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from ._cache import (
        TTLCache,
        DiskCache,
        CacheParams,
        CacheReturn,
        cached,
        auto_cached,
        create_cache,
    )


__all__ = (
    "auto_cached",
    "cached",
    "create_cache",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the cache module."""
    return list(__all__)
