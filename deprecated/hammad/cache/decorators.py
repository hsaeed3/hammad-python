"""hammad.cache.decorators"""

from typing import Callable, Optional, Tuple, Union, overload, TYPE_CHECKING
import inspect
from functools import wraps

from .base_cache import BaseCache, CacheParams, CacheReturn
from .ttl_cache import TTLCache

__all__ = (
    "get_decorator_cache",
    "clear_decorator_cache",
    "cached",
    "auto_cached",
)


# INTERNAL SINGLETON CACHE FOR DECORATORS
_DECORATOR_CACHE: BaseCache | None = None
"""Internal singleton cache for decorators."""


def get_decorator_cache() -> BaseCache:
    """Get the internal singleton cache for decorators."""
    global _DECORATOR_CACHE
    if _DECORATOR_CACHE is None:
        _DECORATOR_CACHE = TTLCache(type="ttl", maxsize=1000, ttl=3600)
    return _DECORATOR_CACHE


def clear_decorator_cache() -> None:
    """Clear the internal singleton cache for decorators."""
    global _DECORATOR_CACHE
    if _DECORATOR_CACHE is not None:
        _DECORATOR_CACHE.clear()
        _DECORATOR_CACHE = None


@overload
def cached(
    func: "Callable[CacheParams, CacheReturn]",
) -> "Callable[CacheParams, CacheReturn]":
    """Decorator with automatic key generation, using the global CACHE."""
    ...


@overload
def cached(
    *,
    key: Optional["Callable[..., str]"] = None,
    ttl: Optional[int] = None,
    maxsize: Optional[int] = None,
    cache: Optional["BaseCache"] = None,
) -> (
    "Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]]"
):
    """Decorator with custom key function and/or cache settings."""
    ...


def cached(
    func: Optional["Callable[CacheParams, CacheReturn]"] = None,
    *,
    key: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
    maxsize: Optional[int] = None,
    cache: Optional["BaseCache"] = None,
) -> Union[
    "Callable[CacheParams, CacheReturn]",
    "Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]]",
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

    effective_cache: BaseCache = get_decorator_cache()

    if cache is not None:
        effective_cache = cache
    elif ttl is not None or maxsize is not None:
        default_maxsize = get_decorator_cache().maxsize
        default_ttl = get_decorator_cache().ttl

        effective_cache = TTLCache(
            type="ttl",
            maxsize=maxsize if maxsize is not None else default_maxsize,
            ttl=ttl if ttl is not None else default_ttl,
        )
    else:
        effective_cache = get_decorator_cache()

    def decorator(
        f_to_decorate: "Callable[CacheParams, CacheReturn]",
    ) -> "Callable[CacheParams, CacheReturn]":
        key_func_to_use: "Callable[..., str]"
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
    cache: Optional["BaseCache"] = None,
) -> (
    "Callable[[Callable[CacheParams, CacheReturn]], Callable[CacheParams, CacheReturn]]"
):
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
        func_to_decorate: "Callable[CacheParams, CacheReturn]",
    ) -> "Callable[CacheParams, CacheReturn]":
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
            effective_cache = cache if cache is not None else get_decorator_cache()
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
