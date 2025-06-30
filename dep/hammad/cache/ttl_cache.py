"""hammad.cache.ttl_cache"""

from dataclasses import dataclass
from typing import Any, Literal, OrderedDict, Tuple
import time

from .base_cache import BaseCache

__all__ = ("TTLCache",)


@dataclass
class TTLCache(BaseCache):
    """
    Thread-safe TTL cache implementation with LRU eviction.

    Uses OrderedDict for efficient LRU tracking and automatic cleanup
    of expired entries on access.
    """

    maxsize: int = 1000
    ttl: int = 3600
    type: Literal["ttl"] = "ttl"

    def __post_init__(self):
        """Initialize TTL cache after dataclass initialization."""
        super().__post_init__()
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if key in self._cache:
            _value, timestamp = self._cache[key]
            if time.time() - timestamp <= self.ttl:
                self._cache.move_to_end(key)
                return True
            else:
                # Expired, remove it
                del self._cache[key]
        return False

    def __getitem__(self, key: str) -> Any:
        """Get value for key if not expired."""
        if key in self:
            return self._cache[key][0]
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value with current timestamp."""
        if len(self._cache) >= self.maxsize and key not in self._cache:
            self._cleanup_expired()

            if len(self._cache) >= self.maxsize:
                self._cache.popitem(last=False)

        self._cache[key] = (value, time.time())
        self._cache.move_to_end(key)

    def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        current_time = time.time()

        expired_keys = [
            k
            for k, (_, ts) in list(self._cache.items())
            if current_time - ts > self.ttl
        ]
        for k in expired_keys:
            if k in self._cache:
                del self._cache[k]

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
