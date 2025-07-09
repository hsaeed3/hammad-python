"""hammad.cache.file_cache"""

from dataclasses import dataclass
from typing import Any, Literal, Optional, TypeAlias, Union
import os
import hashlib
import pickle
from pathlib import Path

from .base_cache import BaseCache

__all__ = ("FileCache", "FileCacheLocation")


FileCacheLocation: TypeAlias = Union[
    # Example .pkl route
    Literal["cache.pkl"], Literal["cache/"], str, Path
]


@dataclass
class FileCache(BaseCache):
    """
    Persistent disk-based cache that stores data in a directory.

    Uses pickle for serialization and automatically uses __pycache__ directory
    if no cache directory is specified.
    """

    location: Optional[str] = None
    type: Literal["file"] = "file"

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
