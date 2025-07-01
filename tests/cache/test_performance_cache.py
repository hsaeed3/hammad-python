import pytest

from hammad.cache.cache import Cache, create_cache
from hammad.cache.decorators import cached, auto_cached
from hammad.cache.file_cache import FileCache
from hammad.cache.ttl_cache import TTLCache

import tempfile
import shutil
from typing import Any, Optional, Type


class DummyType:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, DummyType) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


def dummy_factory(
    target: type,
    name: Optional[str],
    description: Optional[str],
    field_name: Optional[str],
    default: Any,
) -> str:
    # Just return a string representation for testing
    return f"{target.__name__}-{name}-{description}-{field_name}-{default}"


@cached
def cached_factory(
    target: type,
    name: Optional[str],
    description: Optional[str],
    field_name: Optional[str],
    default: Any,
) -> str:
    return dummy_factory(target, name, description, field_name, default)


def test_cached_decorator_auto_hashing_with_complex_args():
    # Use different types and values to test hashing
    t1 = DummyType(1)
    t2 = DummyType(2)
    result1 = cached_factory(DummyType, "A", "desc", "field", 123)
    result2 = cached_factory(DummyType, "A", "desc", "field", 123)
    result3 = cached_factory(DummyType, "B", "desc", "field", 123)
    result4 = cached_factory(DummyType, "A", "desc", "field", 456)
    # Should be cached: result1 and result2
    assert result1 == result2
    # Different name, should not be cached
    assert result1 != result3
    # Different default, should not be cached
    assert result1 != result4


def test_cached_decorator_with_unhashable_args():
    # Should not raise, should still cache based on automatic key
    d = {"a": 1, "b": [1, 2, 3]}

    @cached
    def f(x):
        return x["a"] + len(x["b"])

    r1 = f(d)
    r2 = f({"a": 1, "b": [1, 2, 3]})
    assert r1 == r2


def test_auto_cached_include_and_ignore():
    calls = []

    @auto_cached(include=("x",))
    def f(x, y):
        calls.append((x, y))
        return x + y

    assert f(1, 2) == 3
    assert f(1, 3) == 3  # Should return cached value since only x=1 is used for key
    # Should be cached because only x is included in key
    assert f(1, 2) == 3
    assert calls.count((1, 2)) == 1
    assert (
        calls.count((1, 3)) == 0
    )  # This call should never execute the function due to caching

    calls.clear()

    @auto_cached(ignore=("y",))
    def g(x, y):
        calls.append((x, y))
        return x * y

    assert g(2, 3) == 6
    assert g(2, 4) == 6  # Should return cached value since y is ignored
    # Should be cached because y is ignored
    assert g(2, 3) == 6
    assert g(2, 4) == 6
    assert calls.count((2, 3)) == 1
    assert (
        calls.count((2, 4)) == 0
    )  # This call should never execute the function due to caching


def test_ttlcache_eviction_and_expiry(monkeypatch):
    cache = TTLCache(maxsize=2, ttl=1)

    @cached(cache=cache)
    def f(x):
        return x * 2

    assert f(1) == 2
    assert f(2) == 4
    assert f(1) == 2  # still cached
    assert f(3) == 6  # triggers eviction (maxsize=2)
    # Now, 2 should be evicted (LRU)
    assert 2 not in [k for k, _ in cache._cache.items()]
    # Simulate expiry
    monkeypatch.setattr("time.time", lambda: list(cache._cache.values())[0][1] + 2)
    assert f(1) == 2  # Should recompute, as expired


def test_filecache_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(location=tmpdir)

        @cached(cache=cache)
        def f(x):
            return x + 10

        assert f(5) == 15
        assert f(5) == 15  # Should be cached
        # Remove from memory, reload from disk
        cache2 = FileCache(location=tmpdir)

        @cached(cache=cache2)
        def g(x):
            return x + 10

        assert g(5) == 15  # Should load from disk


def test_cache_factory_ttl_and_disk():
    ttl_cache = Cache(type="ttl", maxsize=5, ttl=10)
    assert isinstance(ttl_cache, TTLCache)
    assert ttl_cache.maxsize == 5
    assert ttl_cache.ttl == 10

    with tempfile.TemporaryDirectory() as tmpdir:
        disk_cache = Cache(type="file", location=tmpdir)
        assert isinstance(disk_cache, FileCache)
        assert disk_cache.location == tmpdir


def test_cache_factory_invalid_type():
    with pytest.raises(ValueError):
        Cache(type="unknown")


def test_filecache_clear(tmp_path):
    cache = FileCache(location=str(tmp_path))

    @cached(cache=cache)
    def f(x):
        return x * 3

    f(1)
    f(2)
    files = list(tmp_path.glob("cache_*.pkl"))
    assert len(files) == 2
    cache.clear()
    files = list(tmp_path.glob("cache_*.pkl"))
    assert len(files) == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
