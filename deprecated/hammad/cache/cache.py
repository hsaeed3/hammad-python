"""hammad.cache.cache"""

from typing import (
    overload,
    TYPE_CHECKING,
    Literal,
    Optional,
    Any,
    Union,
    get_args,
)
from pathlib import Path

from .base_cache import BaseCache, CacheType
from .file_cache import FileCache, FileCacheLocation
from .ttl_cache import TTLCache


__all__ = ("Cache", "create_cache")


class Cache:
    """
    Helper factory class for creating cache instances.

    Example usage:
        ttl_cache = Cache(type="ttl", maxsize=100, ttl=60)
        file_cache = Cache(type="file", location="cache.pkl")
    """

    @overload
    def __new__(
        cls,
        type: Literal["ttl"] = "ttl",
        *,
        maxsize: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> "TTLCache":
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
        cls, type: Literal["file"], *, location: Optional["FileCacheLocation"] = None
    ) -> "FileCache":
        """
        Create a new file cache instance.

        Args:
            type: The type of cache to create.
            location: The directory to store the cache files.

        Returns:
            A new disk cache instance.
        """
        ...

    def __new__(cls, type: "CacheType" = "ttl", **kwargs: Any) -> "BaseCache":
        """
        Create a new cache instance.
        """
        if type == "ttl":
            from .ttl_cache import TTLCache

            valid_ttl_params = {"maxsize", "ttl"}
            ttl_constructor_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in valid_ttl_params and v is not None
            }
            return TTLCache(type=type, **ttl_constructor_kwargs)
        elif type == "file":
            from .file_cache import FileCache

            valid_file_params = {"location"}
            file_constructor_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in valid_file_params and v is not None
            }
            return FileCache(type=type, **file_constructor_kwargs)
        else:
            supported_types_tuple = get_args(CacheType)
            raise ValueError(
                f"Unsupported cache type: {type}. Supported types are: {supported_types_tuple}"
            )


# Factory


@overload
def create_cache(
    type: Literal["ttl"], *, maxsize: int = 128, ttl: Optional[float] = None
) -> "TTLCache": ...


@overload
def create_cache(
    type: Literal["file"],
    *,
    location: Optional["FileCacheLocation"] = None,
    maxsize: int = 128,
) -> "FileCache": ...


@overload
def create_cache(type: "CacheType", **kwargs: Any) -> "BaseCache": ...


def create_cache(type: "CacheType", **kwargs: Any) -> "BaseCache":
    """
    Factory function to create cache instances of different types.

    Args:
        type: The type of cache to create. Can be "ttl" or "file".
        **kwargs: Additional keyword arguments specific to the cache type.

    Returns:
        A cache instance of the specified type.

    Raises:
        ValueError: If an unsupported cache type is provided.

    Examples:
        ```python
        # Create a TTL cache with custom settings
        ttl_cache = create_cache("ttl", maxsize=256, ttl=300)

        # Create a file cache with custom location
        file_cache = create_cache("file", location="/tmp/my_cache", maxsize=1000)
        ```
    """
    if type == "ttl":
        from .ttl_cache import TTLCache

        maxsize = kwargs.pop("maxsize", 128)
        ttl = kwargs.pop("ttl", None)
        if kwargs:
            raise TypeError(
                f"Unexpected keyword arguments for TTL cache: {list(kwargs.keys())}"
            )
        return TTLCache(maxsize=maxsize, ttl=ttl)
    elif type == "file":
        from .file_cache import FileCache

        location = kwargs.pop("location", None)
        # FileCache doesn't support maxsize, so we just ignore it
        kwargs.pop("maxsize", None)
        if kwargs:
            raise TypeError(
                f"Unexpected keyword arguments for file cache: {list(kwargs.keys())}"
            )
        return FileCache(location=location, type=type)
    else:
        valid_types = get_args("CacheType")
        raise ValueError(
            f"Unsupported cache type: {type}. Valid types are: {valid_types}"
        )
