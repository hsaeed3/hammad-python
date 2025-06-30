"""hammad.cache.base_cache"""

from dataclasses import dataclass
import hashlib
import inspect
from typing import Any, Literal, ParamSpec, TypeAlias, TypeVar, get_args

__all__ = (
    "BaseCache",
    "CacheType",
    "CacheParams",
    "CacheReturn",
)


CacheType: TypeAlias = Literal["ttl", "file"]
"""Type of caches that can be created using `hammad`.

- `"ttl"`: Time-to-live cache.
- `"file"`: File-based cache.
"""

CacheParams = ParamSpec("CacheParams")
"""Parameter specification for cache functions."""

CacheReturn = TypeVar("CacheReturn")
"""Return type for cache functions."""


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
