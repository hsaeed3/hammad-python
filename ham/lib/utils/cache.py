"""ham.lib.utils.cache"""

import hashlib
import inspect
import pickle
import time
from collections import OrderedDict
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Optional, TypeVar, Union

__all__ = [
    "cached",
    "clear_cache",
]

# Type variables for better type hints
F = TypeVar("F", bound=Callable[..., Any])

# Global cache registry for clearing
_CACHE_REGISTRY: list["BaseCache"] = []


def make_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments using SHA-256 hashing."""

    def _hash_obj(obj: Any) -> str:
        """Recursively hash any Python object."""
        if obj is None:
            return "None"
        elif isinstance(obj, (bool, int, float, str, bytes)):
            return f"{type(obj).__name__}:{obj}"
        elif isinstance(obj, (list, tuple)):
            items = [_hash_obj(item) for item in obj]
            return f"{type(obj).__name__}:[{','.join(items)}]"
        elif isinstance(obj, set):
            items = [_hash_obj(item) for item in sorted(obj, key=str)]
            return f"set:{{{','.join(items)}}}"
        elif isinstance(obj, dict):
            pairs = [
                f"{_hash_obj(k)}:{_hash_obj(v)}"
                for k, v in sorted(obj.items(), key=lambda x: str(x[0]))
            ]
            return f"dict:{{{','.join(pairs)}}}"
        elif callable(obj):
            module = getattr(obj, "__module__", "unknown")
            name = getattr(obj, "__qualname__", getattr(obj, "__name__", "unknown"))
            return f"callable:{module}.{name}"
        elif hasattr(obj, "__dict__"):
            class_name = f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"
            return f"object:{class_name}:{_hash_obj(obj.__dict__)}"
        else:
            return f"{type(obj).__name__}:{repr(obj)}"

    # Combine args and kwargs into a single hashable representation
    key_parts = [_hash_obj(arg) for arg in args]
    key_parts.extend(f"{k}={_hash_obj(v)}" for k, v in sorted(kwargs.items()))
    key_str = f"({','.join(key_parts)})"

    # Return SHA-256 hash for consistent key length
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()


class BaseCache:
    """Base cache interface."""

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0
        self._lock = RLock()

    def __getitem__(self, key: str) -> Any:
        raise NotImplementedError

    def __setitem__(self, key: str, value: Any) -> None:
        raise NotImplementedError

    def __delitem__(self, key: str) -> None:
        raise NotImplementedError

    def __contains__(self, key: str) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class LRUCache(BaseCache):
    """Least Recently Used (LRU) cache implementation using OrderedDict."""

    def __init__(self, maxsize: int):
        super().__init__(maxsize)
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                raise KeyError(key)
            # Move to end to mark as recently used
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                # Update existing key
                self._cache.move_to_end(key)
            self._cache[key] = value
            # Evict oldest item if over capacity
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._cache[key]

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0


class TTLCache(BaseCache):
    """Time-To-Live cache implementation."""

    def __init__(self, maxsize: int, ttl: float):
        super().__init__(maxsize)
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cached item has expired."""
        return time.time() - timestamp > self.ttl

    def _evict_expired(self) -> None:
        """Remove all expired items."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                raise KeyError(key)

            value, timestamp = self._cache[key]

            # Check if expired
            if self._is_expired(timestamp):
                del self._cache[key]
                self.misses += 1
                raise KeyError(key)

            # Move to end to mark as recently used
            self._cache.move_to_end(key)
            self.hits += 1
            return value

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            # Evict expired items first
            self._evict_expired()

            timestamp = time.time()
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, timestamp)

            # Evict oldest item if over capacity
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._cache[key]

    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            _, timestamp = self._cache[key]
            if self._is_expired(timestamp):
                del self._cache[key]
                return False
            return True

    def __len__(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0


class PersistentCache(LRUCache):
    """LRU cache with optional persistence to disk."""

    def __init__(self, maxsize: int, path: Optional[Path] = None):
        super().__init__(maxsize)
        self.path = path
        if path:
            self.path = Path(path)
            self._load()

    def _load(self) -> None:
        """Load cache from disk if file exists."""
        if self.path and self.path.exists():
            try:
                with open(self.path, "rb") as f:
                    data = pickle.load(f)
                    self._cache.update(data)
            except (pickle.PickleError, OSError):
                # If loading fails, start with empty cache
                pass

    def _save(self) -> None:
        """Save cache to disk."""
        if self.path:
            try:
                # Ensure parent directory exists
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "wb") as f:
                    pickle.dump(dict(self._cache), f)
            except (pickle.PickleError, OSError):
                # Silently ignore save errors
                pass

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item and save to disk if persistence is enabled."""
        super().__setitem__(key, value)
        self._save()

    def __delitem__(self, key: str) -> None:
        """Delete item and save to disk if persistence is enabled."""
        super().__delitem__(key)
        self._save()

    def clear(self) -> None:
        """Clear cache and save to disk if persistence is enabled."""
        super().clear()
        self._save()


def cached(
    func: Optional[F] = None,
    *,
    maxsize: int = 128,
    ttl: Optional[float] = None,
    key: Optional[Callable[..., str]] = None,
    path: Optional[Union[str, Path]] = None,
    typed: bool = False,
    ignore: Optional[tuple[str, ...]] = None,
    include: Optional[tuple[str, ...]] = None,
) -> Union[F, Callable[[F], F]]:
    """
    Flexible caching decorator with optional persistence.

    Args:
        func: Function to cache (when used without parentheses)
        maxsize: Maximum cache size (default: 128)
        ttl: Time-to-live in seconds (default: None = no expiration)
        key: Custom key function (default: None = auto-generate)
        path: Path to persist cache (default: None = memory only)
        typed: If True, arguments of different types cached separately
        ignore: Parameter names to exclude from cache key
        include: Parameter names to include in cache key (excludes others)

    Returns:
        Decorated function with caching

    Examples:
        # Simple usage
        @cached
        def expensive_func(x, y):
            return x + y

        # With TTL
        @cached(ttl=60)
        def api_call(endpoint):
            return requests.get(endpoint)

        # With persistence
        @cached(path="cache/my_func.pkl")
        def process_data(data):
            return heavy_computation(data)

        # Ignore certain parameters
        @cached(ignore=("debug", "logger"))
        def fetch_user(user_id, debug=False, logger=None):
            return get_user_from_db(user_id)

        # Include only specific parameters
        @cached(include=("user_id",))
        def get_profile(user_id, include_posts=False, include_comments=False):
            return fetch_profile(user_id)
    """

    if ignore and include:
        raise ValueError("Cannot specify both 'ignore' and 'include'")

    def decorator(f: F) -> F:
        # Unwrap classmethod/staticmethod to get the actual function
        actual_func = f
        is_classmethod = isinstance(f, classmethod)
        is_staticmethod = isinstance(f, staticmethod)

        if is_classmethod:
            actual_func = f.__func__
        elif is_staticmethod:
            actual_func = f.__func__

        # Create appropriate cache based on parameters
        if ttl is not None:
            # Use TTL cache
            cache = TTLCache(maxsize=maxsize, ttl=ttl)
        elif path is not None:
            # Use persistent cache
            cache_path = Path(path) if isinstance(path, str) else path
            cache = PersistentCache(maxsize=maxsize, path=cache_path)
        else:
            # Use regular LRU cache
            cache = LRUCache(maxsize=maxsize)

        # Register cache for clearing
        _CACHE_REGISTRY.append(cache)

        # Determine key function
        if key is not None:
            key_func = key
        else:
            # Auto-generate key function using the actual function
            sig = inspect.signature(actual_func)

            def auto_key(*args, **kwargs) -> str:
                # Bind arguments
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                # Filter parameters based on ignore/include
                params = bound.arguments.copy()

                if include is not None:
                    params = {k: v for k, v in params.items() if k in include}
                elif ignore is not None:
                    params = {k: v for k, v in params.items() if k not in ignore}

                # Add function identity to key
                func_id = f"{actual_func.__module__}.{actual_func.__qualname__}"

                # Add type information if typed=True
                if typed:
                    type_info = tuple((type(v).__name__ for v in params.values()))
                    return f"{func_id}:{make_cache_key(**params)}:{type_info}"

                return f"{func_id}:{make_cache_key(**params)}"

            key_func = auto_key

        @wraps(actual_func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_func(*args, **kwargs)

            # Try to get from cache
            try:
                return cache[cache_key]
            except KeyError:
                # Compute and cache result
                result = actual_func(*args, **kwargs)

                # Try to cache the result
                try:
                    # Test if the result is picklable before caching
                    pickle.dumps(result)
                    cache[cache_key] = result
                except (pickle.PickleError, TypeError, AttributeError):
                    # If result can't be pickled, just return it without caching
                    pass

                return result

        # Attach cache to function for introspection
        wrapper._cache = cache
        wrapper._cache_info = lambda: {
            "size": len(cache),
            "maxsize": cache.maxsize,
            "hits": cache.hits,
            "misses": cache.misses,
        }
        wrapper._cache_clear = cache.clear

        # If original was classmethod/staticmethod, wrap back
        if is_classmethod:
            return classmethod(wrapper)
        elif is_staticmethod:
            return staticmethod(wrapper)

        return wrapper

    # Handle both @cached and @cached(...) syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


def clear_cache() -> None:
    """Clear all registered caches."""
    for cache in _CACHE_REGISTRY:
        cache.clear()
    _CACHE_REGISTRY.clear()
