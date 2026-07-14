import pytest
import tempfile
import os
from pathlib import Path
from ham.core.cache import Cache, create_cache
from ham.core.cache.ttl_cache import TTLCache
from ham.core.cache.file_cache import FileCache


class TestCache:
    """Test cases for the Cache factory class."""

    def test_cache_ttl_creation(self):
        """Test creating a TTL cache using Cache class."""
        cache = Cache(type="ttl", maxsize=100, ttl=60)
        assert isinstance(cache, TTLCache)
        assert cache.maxsize == 100
        assert cache.ttl == 60

    def test_cache_ttl_default(self):
        """Test creating a TTL cache with default parameters."""
        cache = Cache(type="ttl")
        assert isinstance(cache, TTLCache)

    def test_cache_file_default(self):
        """Test creating a file cache with default location."""
        cache = Cache(type="file")
        assert isinstance(cache, FileCache)

    def test_cache_invalid_type(self):
        """Test that invalid cache type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported cache type"):
            Cache(type="invalid")


class TestCreateCache:
    """Test cases for the create_cache factory function."""

    def test_create_ttl_cache(self):
        """Test creating a TTL cache using create_cache function."""
        cache = create_cache("ttl", maxsize=256, ttl=300)
        assert isinstance(cache, TTLCache)
        assert cache.maxsize == 256
        assert cache.ttl == 300

    def test_create_ttl_cache_defaults(self):
        """Test creating a TTL cache with default parameters."""
        cache = create_cache("ttl")
        assert isinstance(cache, TTLCache)
        assert cache.maxsize == 128
        assert cache.ttl is None

    def test_create_file_cache_default_location(self):
        """Test creating a file cache with default location."""
        cache = create_cache("file")
        assert isinstance(cache, FileCache)

    def test_create_cache_invalid_type(self):
        """Test that invalid cache type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported cache type"):
            create_cache("invalid")

    def test_create_ttl_cache_unexpected_kwargs(self):
        """Test that unexpected kwargs for TTL cache raises TypeError."""
        with pytest.raises(TypeError, match="Unexpected keyword arguments"):
            create_cache("ttl", invalid_param=True)

    def test_create_file_cache_unexpected_kwargs(self):
        """Test that unexpected kwargs for file cache raises TypeError."""
        with pytest.raises(TypeError, match="Unexpected keyword arguments"):
            create_cache("file", invalid_param=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
