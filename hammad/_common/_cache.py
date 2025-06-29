"""hammad._common._utils._cache"""

# Internal cache used within the library
from ..cache.ttl_cache import TTLCache

__all__ = ("_get_cache", "_clear_cache")


_cache : TTLCache | None = None
"""Internal cache used within the library."""


def _get_cache() -> TTLCache:
    """Get the internal cache."""
    global _cache
    if _cache is None:
        _cache = TTLCache(maxsize=1000, ttl=3600)
    return _cache


def _clear_cache() -> None:
    """Clear the internal cache."""
    global _cache
    if _cache is not None:
        _cache.clear()
        _cache = None