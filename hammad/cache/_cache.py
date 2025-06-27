"""hammad.cache._cache

Contains helpful resources for creating simple cache systems, and
decorators that implement "automatic" hashing & caching of function calls.
"""

from __future__ import annotations

import hashlib
import os
from functools import wraps
import inspect
import pickle
import time
from dataclasses import dataclass
from collections import OrderedDict
from pathlib import Path
from typing import (
    Any,
    Callable,
    TypeVar,
    Tuple,
    Optional,
    overload,
    ParamSpec,
    Literal,
    get_args,
    TypeAlias,
    Union,
    overload,
)

__all__ = [
    "cached",
    "auto_cached",
    "Cache",
    "TTLCache",
    "DiskCache",
    "CacheType",
    "CacheParams",
    "CacheReturn",
    "create_cache",
]


# -----------------------------------------------------------------------------
# TYPES
# -----------------------------------------------------------------------------

CacheType: TypeAlias = Literal["ttl", "disk"]
"""Type of caches that can be created using `hammad`.

- `"ttl"`: Time-to-live cache.
- `"disk"`: Disk-based cache.
"""

CacheParams = ParamSpec("CacheParams")
"""Parameter specification for cache functions."""

CacheReturn = TypeVar("CacheReturn")
"""Return type for cache functions."""


# -----------------------------------------------------------------------------
# GLOBAL (Internal) CACHE
# -----------------------------------------------------------------------------


_hammad_CACHE: None | BaseCache = None
"""Internal cache for the `hammad` package. Instantiated when needed."""


def _get_cache() -> BaseCache:
    """Returns the global cache instance, creating it if necessary."""
    global _hammad_CACHE
    if _hammad_CACHE is None:
        _hammad_CACHE = TTLCache(maxsize=1000, ttl=3600)
    return _hammad_CACHE


# -----------------------------------------------------------------------------
# BASE
# -----------------------------------------------------------------------------


@dataclass
class BaseCache:
    """Base class for all caches created using `hammad`."""

    type: CacheType
    """Type of cache."""

    def __post_init__(self) -> None:
        """Post-initialization hook."""
        if self.type not in get_args(CacheType):
            raise ValueError(f"Invalid cache type: {self.type}")

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError("Subclasses must implement __contains__")

    def __getitem__(self, key: str) -> Any:
        """Get value for key."""
        raise NotImplementedError("Subclasses must implement __getitem__")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value for key."""
        raise NotImplementedError("Subclasses must implement __setitem__")

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default if key doesn't exist."""
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        """Clear all cached items."""
        raise NotImplementedError("Subclasses must implement clear")

    def make_hashable(self, obj: Any) -> str:
        """
        Convert any object to a stable hash string.

        Uses SHA-256 to generate consistent hash representations.
        Handles nested structures recursively.

        Args:
            obj: Object to hash

        Returns:
            Hexadecimal hash string
        """

        def _hash_obj(data: Any) -> str:
            """Internal recursive hashing function with memoization."""
            # Handle None first
            if data is None:
                return "null"

            if isinstance(data, bool):
                return f"bool:{data}"
            elif isinstance(data, int):
                return f"int:{data}"
            elif isinstance(data, float):
                if data != data:  # NaN
                    return "float:nan"
                elif data == float("inf"):
                    return "float:inf"
                elif data == float("-inf"):
                    return "float:-inf"
                else:
                    return f"float:{data}"
            elif isinstance(data, str):
                return f"str:{data}"
            elif isinstance(data, bytes):
                return f"bytes:{data.hex()}"

            # Handle collections
            elif isinstance(data, (list, tuple)):
                collection_type = "list" if isinstance(data, list) else "tuple"
                items = [_hash_obj(item) for item in data]
                return f"{collection_type}:[{','.join(items)}]"

            elif isinstance(data, set):
                try:
                    sorted_items = sorted(data, key=lambda x: str(x))
                except TypeError:
                    sorted_items = sorted(
                        data, key=lambda x: (type(x).__name__, str(x))
                    )
                items = [_hash_obj(item) for item in sorted_items]
                return f"set:{{{','.join(items)}}}"

            elif isinstance(data, dict):
                try:
                    sorted_items = sorted(data.items(), key=lambda x: str(x[0]))
                except TypeError:
                    # Fallback for non-comparable keys
                    sorted_items = sorted(
                        data.items(), key=lambda x: (type(x[0]).__name__, str(x[0]))
                    )
                pairs = [f"{_hash_obj(k)}:{_hash_obj(v)}" for k, v in sorted_items]
                return f"dict:{{{','.join(pairs)}}}"

            elif isinstance(data, type):
                module = getattr(data, "__module__", "builtins")
                qualname = getattr(data, "__qualname__", data.__name__)
                return f"type:{module}.{qualname}"

            elif callable(data):
                module = getattr(data, "__module__", "unknown")
                qualname = getattr(
                    data, "__qualname__", getattr(data, "__name__", "unknown_callable")
                )

                try:
                    source = inspect.getsource(data)
                    normalized_source = " ".join(source.split())
                    return f"callable:{module}.{qualname}:{hash(normalized_source)}"
                except (OSError, TypeError, IndentationError):
                    return f"callable:{module}.{qualname}"

            elif hasattr(data, "__dict__"):
                class_info = (
                    f"{data.__class__.__module__}.{data.__class__.__qualname__}"
                )
                obj_dict = {"__class__": class_info, **data.__dict__}
                return f"object:{_hash_obj(obj_dict)}"

            elif hasattr(data, "__slots__"):
                class_info = (
                    f"{data.__class__.__module__}.{data.__class__.__qualname__}"
                )
                slot_dict = {
                    slot: getattr(data, slot, None)
                    for slot in data.__slots__
                    if hasattr(data, slot)
                }
                obj_dict = {"__class__": class_info, **slot_dict}
                return f"slotted_object:{_hash_obj(obj_dict)}"

            else:
                try:
                    repr_str = repr(data)
                    return f"repr:{type(data).__name__}:{repr_str}"
                except Exception:
                    # Ultimate fallback
                    return f"unknown:{type(data).__name__}:{id(data)}"

        # Generate the hash representation
        hash_representation = _hash_obj(obj)

        # Create final SHA-256 hash
        return hashlib.sha256(
            hash_representation.encode("utf-8", errors="surrogatepass")
        ).hexdigest()


# -----------------------------------------------------------------------------
# TTL CACHE
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# DISK CACHE
# -----------------------------------------------------------------------------


@dataclass
class DiskCache(BaseCache):
    """
    Persistent disk-based cache that stores data in a directory.

    Uses pickle for serialization and automatically uses __pycache__ directory
    if no cache directory is specified.
    """

    location: Optional[str] = None
    type: Literal["disk"] = "disk"

    def __post_init__(self):
        """Initialize disk cache after dataclass initialization."""
        super().__post_init__()
        if self.location is None:
            self.location = os.path.join(os.getcwd(), "__pycache__")

        self.location_path = Path(self.location)
        self.location_path.mkdir(exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        safe_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.location_path / f"cache_{safe_key}.pkl"

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._get_cache_path(key).exists()

    def __getitem__(self, key: str) -> Any:
        """Get value for key."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            raise KeyError(key)

        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, OSError) as e:
            cache_path.unlink(missing_ok=True)
            raise KeyError(key) from e

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value for key."""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(value, f)
        except (pickle.PickleError, OSError) as e:
            cache_path.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to cache value for key '{key}': {e}") from e

    def clear(self) -> None:
        """Clear all cached items."""
        for cache_file in self.location_path.glob("cache_*.pkl"):
            try:
                cache_file.unlink()
            except OSError:
                pass


# -----------------------------------------------------------------------------
# Primary `Cache` Class -- Used For Factory Initialization
# -----------------------------------------------------------------------------


class Cache:
    """
    Helper factory class for creating cache instances.

    Example usage:
        ttl_cache = Cache(type="ttl", maxsize=100, ttl=60)
        disk_cache = Cache(type="disk", location="/tmp/cache")
    """

    @overload
    def __new__(
        cls,
        type: Literal["ttl"] = "ttl",
        *,
        maxsize: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> TTLCache:
        """
        Create a new TTL (Time To Live) cache instance.

        Args:
            type: The type of cache to create.
            maxsize: The maximum number of items to store in the cache.
            ttl: The time to live for items in the cache.

        Returns:
            A new TTL cache instance.
        """
        ...

    @overload
    def __new__(
        cls, type: Literal["disk"], *, location: Optional[str] = None
    ) -> DiskCache:
        """
        Create a new disk cache instance.

        Args:
            type: The type of cache to create.
            location: The directory to store the cache files.

        Returns:
            A new disk cache instance.
        """
        ...

    def __new__(cls, type: CacheType = "ttl", **kwargs: Any) -> BaseCache:
        """
        Create a new cache instance.
        """
        if type == "ttl":
            valid_ttl_params = {"maxsize", "ttl"}
            ttl_constructor_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in valid_ttl_params and v is not None
            }
            return TTLCache(type=type, **ttl_constructor_kwargs)
        elif type == "disk":
            valid_disk_params = {"location"}
            disk_constructor_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in valid_disk_params and v is not None
            }
            return DiskCache(type=type, **disk_constructor_kwargs)
        else:
            supported_types_tuple = get_args(CacheType)
            raise ValueError(
                f"Unsupported cache type: {type}. Supported types are: {supported_types_tuple}"
            )


# -----------------------------------------------------------------------------
# Decorators
# -----------------------------------------------------------------------------


@overload
def cached(
    func: Callable[CacheParams, CacheReturn],
) -> Callable[CacheParams, CacheReturn]:
    """Decorator with automatic key generation, using the global CACHE."""
    ...


@overload
def cached(
    *,
    key: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
    maxsize: Optional[int] = None,
    cache: Optional[BaseCache] = None,
) -> Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]]:
    """Decorator with custom key function and/or cache settings."""
    ...


def cached(
    func: Optional[Callable[CacheParams, CacheReturn]] = None,
    *,
    key: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
    maxsize: Optional[int] = None,
    cache: Optional[BaseCache] = None,
) -> Union[
    Callable[CacheParams, CacheReturn],
    Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]],
]:
    """
    Flexible caching decorator that preserves type hints and signatures.

    Can be used with or without arguments:
    - `@cached`: Uses automatic key generation with the global `hammad.cache.CACHE`.
    - `@cached(key=custom_key_func)`: Uses a custom key generation function.
    - `@cached(ttl=300, maxsize=50)`: Creates a new `TTLCache` instance specifically
      for the decorated function with the given TTL and maxsize.
    - `@cached(cache=my_cache_instance)`: Uses a user-provided cache instance.

    Args:
        func: The function to be cached (implicitly passed when used as `@cached`).
        key: An optional function that takes the same arguments as `func` and
             returns a string key. If `None`, a key is automatically generated.
        ttl: Optional. Time-to-live in seconds. If `cache` is not provided and `ttl`
             or `maxsize` is set, a new `TTLCache` is created for this function using
             these settings.
        maxsize: Optional. Maximum number of items in the cache. See `ttl`.
        cache: Optional. A specific cache instance (conforming to `BaseCache`)
               to use. If provided, `ttl` and `maxsize` arguments (intended for
               creating a new per-function cache) are ignored, as the provided
               cache instance manages its own lifecycle and capacity.

    Returns:
        The decorated function with caching capabilities.
    """
    effective_cache: BaseCache = _get_cache()

    if cache is not None:
        effective_cache = cache
    elif ttl is not None or maxsize is not None:
        default_maxsize = _get_cache().maxsize
        default_ttl = _get_cache().ttl

        effective_cache = TTLCache(
            type="ttl",
            maxsize=maxsize if maxsize is not None else default_maxsize,
            ttl=ttl if ttl is not None else default_ttl,
        )
    else:
        effective_cache = _get_cache()

    def decorator(
        f_to_decorate: Callable[CacheParams, CacheReturn],
    ) -> Callable[CacheParams, CacheReturn]:
        key_func_to_use: Callable[..., str]
        if key is None:
            sig = inspect.signature(f_to_decorate)

            def auto_key_func(
                *args: CacheParams.args, **kwargs: CacheParams.kwargs
            ) -> str:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                key_parts = []
                for param_name, param_value in bound_args.arguments.items():
                    key_parts.append(
                        f"{param_name}={effective_cache.make_hashable(param_value)}"
                    )

                return f"{f_to_decorate.__module__}.{f_to_decorate.__qualname__}({','.join(key_parts)})"

            key_func_to_use = auto_key_func
        else:
            key_func_to_use = key

        @wraps(f_to_decorate)
        def wrapper(
            *args: CacheParams.args, **kwargs: CacheParams.kwargs
        ) -> CacheReturn:
            try:
                cache_key_value = key_func_to_use(*args, **kwargs)

                if cache_key_value in effective_cache:
                    return effective_cache[cache_key_value]

                result = f_to_decorate(*args, **kwargs)
                effective_cache[cache_key_value] = result
                return result

            except Exception:
                return f_to_decorate(*args, **kwargs)

        setattr(wrapper, "__wrapped__", f_to_decorate)
        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def auto_cached(
    *,
    ignore: Optional[Tuple[str, ...]] = None,
    include: Optional[Tuple[str, ...]] = None,
    ttl: Optional[int] = None,
    maxsize: Optional[int] = None,
    cache: Optional[BaseCache] = None,
) -> Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]]:
    """
    Advanced caching decorator with automatic parameter selection for key generation.

    Automatically generates cache keys based on a selection of the function's
    parameters. This decorator internally uses the `cached` decorator.

    Args:
        ignore: A tuple of parameter names to exclude from cache key generation.
                Cannot be used with `include`.
        include: A tuple of parameter names to exclusively include in cache key
                 generation. All other parameters will be ignored. Cannot be used
                 with `ignore`.
        ttl: Optional. Time-to-live in seconds. Passed to the underlying `cached`
             decorator. If `cache` is not provided, this can lead to the creation
             of a new `TTLCache` for the decorated function.
        maxsize: Optional. Max cache size. Passed to `cached`. See `ttl`.
        cache: Optional. A specific cache instance (conforming to `BaseCache`)
               to use. This is passed directly to the underlying `cached` decorator.
               If provided, `ttl` and `maxsize` arguments might be interpreted
               differently by `cached` (see `cached` docstring).

    Returns:
        A decorator function that, when applied, will cache the results of
        the decorated function.

    Example:
        ```python
        from hammad.cache import auto_cached, create_cache

        # Example of using a custom cache instance
        my_user_cache = create_cache(cache_type="ttl", ttl=600, maxsize=50)

        @auto_cached(ignore=('debug_mode', 'logger'), cache=my_user_cache)
        def fetch_user_data(user_id: int, debug_mode: bool = False, logger: Any = None):
            # ... expensive operation to fetch data ...
            print(f"Fetching data for user {user_id}")
            return {"id": user_id, "data": "some_data"}

        # Example of per-function TTL without a pre-defined cache
        @auto_cached(include=('url',), ttl=30)
        def fetch_url_content(url: str, timeout: int = 10):
            # ... expensive operation to fetch URL ...
            print(f"Fetching content from {url}")
            return f"Content from {url}"
        ```
    """
    if ignore and include:
        raise ValueError("Cannot specify both 'ignore' and 'include' in auto_cached")

    def actual_decorator(
        func_to_decorate: Callable[CacheParams, CacheReturn],
    ) -> Callable[CacheParams, CacheReturn]:
        sig = inspect.signature(func_to_decorate)

        def auto_key_generator(
            *args: CacheParams.args, **kwargs: CacheParams.kwargs
        ) -> str:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            params_for_key = bound_args.arguments.copy()

            if include is not None:
                params_for_key = {
                    k: v for k, v in params_for_key.items() if k in include
                }
            elif ignore is not None:
                params_for_key = {
                    k: v for k, v in params_for_key.items() if k not in ignore
                }

            # Use the effective cache's make_hashable method
            effective_cache = cache if cache is not None else _get_cache()
            key_parts = [
                f"{k}={effective_cache.make_hashable(v)}"
                for k, v in sorted(params_for_key.items())
            ]
            return f"{func_to_decorate.__module__}.{func_to_decorate.__qualname__}({','.join(key_parts)})"

        configured_cached_decorator = cached(
            key=auto_key_generator, ttl=ttl, maxsize=maxsize, cache=cache
        )
        return configured_cached_decorator(func_to_decorate)

    return actual_decorator


# -----------------------------------------------------------------------------
# CACHE FACTORY
# -----------------------------------------------------------------------------


@overload
def create_cache(
    cache_type: Literal["ttl"], *, maxsize: int = 128, ttl: Optional[float] = None
) -> TTLCache: ...


@overload
def create_cache(
    cache_type: Literal["disk"],
    *,
    cache_dir: Optional[Union[str, Path]] = None,
    maxsize: int = 128,
) -> DiskCache: ...


@overload
def create_cache(cache_type: CacheType, **kwargs: Any) -> BaseCache: ...


def create_cache(cache_type: CacheType, **kwargs: Any) -> BaseCache:
    """
    Factory function to create cache instances of different types.

    Args:
        cache_type: The type of cache to create. Can be "ttl" or "disk".
        **kwargs: Additional keyword arguments specific to the cache type.

    Returns:
        A cache instance of the specified type.

    Raises:
        ValueError: If an unsupported cache type is provided.

    Examples:
        ```python
        # Create a TTL cache with custom settings
        ttl_cache = create_cache("ttl", maxsize=256, ttl=300)

        # Create a disk cache with custom directory
        disk_cache = create_cache("disk", cache_dir="/tmp/my_cache", maxsize=1000)
        ```
    """
    if cache_type == "ttl":
        maxsize = kwargs.pop("maxsize", 128)
        ttl = kwargs.pop("ttl", None)
        if kwargs:
            raise TypeError(
                f"Unexpected keyword arguments for TTL cache: {list(kwargs.keys())}"
            )
        return TTLCache(maxsize=maxsize, ttl=ttl)
    elif cache_type == "disk":
        cache_dir = kwargs.pop("cache_dir", None)
        maxsize = kwargs.pop("maxsize", 128)
        if kwargs:
            raise TypeError(
                f"Unexpected keyword arguments for disk cache: {list(kwargs.keys())}"
            )
        return DiskCache(cache_dir=cache_dir, maxsize=maxsize)
    else:
        valid_types = get_args(CacheType)
        raise ValueError(
            f"Unsupported cache type: {cache_type}. Valid types are: {valid_types}"
        )
