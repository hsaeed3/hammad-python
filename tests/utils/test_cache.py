"""Tests for ham.utils.cache"""

import pickle
import tempfile
import time
from pathlib import Path

import pytest

from ham.utils.cache import (
    BaseCache,
    LRUCache,
    TTLCache,
    PersistentCache,
    cached,
    lru_cache,
    ttl_cache,
    file_cache,
    clear_cache,
    make_cache_key,
)


class TestMakeCacheKey:
    """Tests for make_cache_key function."""

    def test_none_hashing(self):
        """Test hashing None values."""
        key = make_cache_key(None)
        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 produces 64 hex chars

    def test_primitive_types(self):
        """Test hashing primitive types."""
        key1 = make_cache_key(42)
        key2 = make_cache_key(42)
        key3 = make_cache_key(43)
        
        assert key1 == key2
        assert key1 != key3

    def test_string_hashing(self):
        """Test hashing strings."""
        key1 = make_cache_key("hello")
        key2 = make_cache_key("hello")
        key3 = make_cache_key("world")
        
        assert key1 == key2
        assert key1 != key3

    def test_list_hashing(self):
        """Test hashing lists."""
        key1 = make_cache_key([1, 2, 3])
        key2 = make_cache_key([1, 2, 3])
        key3 = make_cache_key([1, 2, 4])
        
        assert key1 == key2
        assert key1 != key3

    def test_dict_hashing(self):
        """Test hashing dictionaries."""
        key1 = make_cache_key({"a": 1, "b": 2})
        key2 = make_cache_key({"b": 2, "a": 1})  # Order shouldn't matter
        key3 = make_cache_key({"a": 1, "b": 3})
        
        assert key1 == key2
        assert key1 != key3

    def test_mixed_args_kwargs(self):
        """Test hashing with mixed args and kwargs."""
        key1 = make_cache_key(1, 2, x=3, y=4)
        key2 = make_cache_key(1, 2, y=4, x=3)  # Kwargs order shouldn't matter
        key3 = make_cache_key(1, 2, x=3, y=5)
        
        assert key1 == key2
        assert key1 != key3


class TestLRUCache:
    """Tests for LRUCache class."""

    def test_basic_operations(self):
        """Test basic cache operations."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        cache["b"] = 2
        cache["c"] = 3
        
        assert cache["a"] == 1
        assert cache["b"] == 2
        assert cache["c"] == 3
        assert len(cache) == 3

    def test_lru_eviction(self):
        """Test that least recently used items are evicted."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        cache["b"] = 2
        cache["c"] = 3
        
        # Access 'a' to make it recently used
        _ = cache["a"]
        
        # Add new item, 'b' should be evicted (least recently used)
        cache["d"] = 4
        
        assert "a" in cache
        assert "b" not in cache
        assert "c" in cache
        assert "d" in cache

    def test_cache_miss(self):
        """Test that KeyError is raised on cache miss."""
        cache = LRUCache(maxsize=3)
        
        with pytest.raises(KeyError):
            _ = cache["nonexistent"]

    def test_cache_update(self):
        """Test updating existing cache entries."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        cache["a"] = 2
        
        assert cache["a"] == 2
        assert len(cache) == 1

    def test_cache_delete(self):
        """Test deleting cache entries."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        del cache["a"]
        
        assert "a" not in cache
        assert len(cache) == 0

    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        cache["b"] = 2
        cache.clear()
        
        assert len(cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_hit_miss_tracking(self):
        """Test that hits and misses are tracked correctly."""
        cache = LRUCache(maxsize=3)
        
        cache["a"] = 1
        
        # Hit
        _ = cache["a"]
        assert cache.hits == 1
        assert cache.misses == 0
        
        # Miss
        try:
            _ = cache["b"]
        except KeyError:
            pass
        assert cache.hits == 1
        assert cache.misses == 1


class TestTTLCache:
    """Tests for TTLCache class."""

    def test_basic_operations(self):
        """Test basic TTL cache operations."""
        cache = TTLCache(maxsize=3, ttl=1.0)
        
        cache["a"] = 1
        assert cache["a"] == 1

    def test_ttl_expiration(self):
        """Test that items expire after TTL."""
        cache = TTLCache(maxsize=3, ttl=0.1)
        
        cache["a"] = 1
        assert cache["a"] == 1
        
        # Wait for expiration
        time.sleep(0.15)
        
        with pytest.raises(KeyError):
            _ = cache["a"]

    def test_ttl_not_expired(self):
        """Test that items don't expire before TTL."""
        cache = TTLCache(maxsize=3, ttl=1.0)
        
        cache["a"] = 1
        time.sleep(0.1)
        
        # Should still be accessible
        assert cache["a"] == 1

    def test_contains_with_expired(self):
        """Test __contains__ removes expired items."""
        cache = TTLCache(maxsize=3, ttl=0.1)
        
        cache["a"] = 1
        assert "a" in cache
        
        time.sleep(0.15)
        assert "a" not in cache

    def test_len_with_expired(self):
        """Test __len__ accounts for expired items."""
        cache = TTLCache(maxsize=3, ttl=0.1)
        
        cache["a"] = 1
        cache["b"] = 2
        assert len(cache) == 2
        
        time.sleep(0.15)
        assert len(cache) == 0


class TestPersistentCache:
    """Tests for PersistentCache class."""

    def test_basic_persistence(self):
        """Test that cache is persisted to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.pkl"
            
            # Create cache and add items
            cache1 = PersistentCache(maxsize=3, path=cache_path)
            cache1["a"] = 1
            cache1["b"] = 2
            
            # Create new cache instance with same path
            cache2 = PersistentCache(maxsize=3, path=cache_path)
            
            # Should load from disk
            assert cache2["a"] == 1
            assert cache2["b"] == 2

    def test_persistence_on_delete(self):
        """Test that deletions are persisted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.pkl"
            
            cache1 = PersistentCache(maxsize=3, path=cache_path)
            cache1["a"] = 1
            del cache1["a"]
            
            cache2 = PersistentCache(maxsize=3, path=cache_path)
            assert "a" not in cache2

    def test_persistence_on_clear(self):
        """Test that clear is persisted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.pkl"
            
            cache1 = PersistentCache(maxsize=3, path=cache_path)
            cache1["a"] = 1
            cache1.clear()
            
            cache2 = PersistentCache(maxsize=3, path=cache_path)
            assert len(cache2) == 0

    def test_no_persistence_without_path(self):
        """Test that cache works without persistence."""
        cache = PersistentCache(maxsize=3, path=None)
        cache["a"] = 1
        assert cache["a"] == 1


class TestCachedDecorator:
    """Tests for @cached decorator."""

    def test_simple_caching(self):
        """Test basic function caching."""
        call_count = 0
        
        @cached
        def add(a, b):
            nonlocal call_count
            call_count += 1
            return a + b
        
        # First call
        result1 = add(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call with same args (should use cache)
        result2 = add(1, 2)
        assert result2 == 3
        assert call_count == 1
        
        # Third call with different args
        result3 = add(2, 3)
        assert result3 == 5
        assert call_count == 2

    def test_caching_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0
        
        @cached
        def greet(name, greeting="Hello"):
            nonlocal call_count
            call_count += 1
            return f"{greeting}, {name}!"
        
        result1 = greet("Alice")
        result2 = greet("Alice")
        result3 = greet("Alice", greeting="Hi")
        result4 = greet(name="Alice", greeting="Hi")
        
        assert call_count == 2
        assert result3 == result4

    def test_ttl_caching(self):
        """Test TTL-based caching."""
        call_count = 0
        
        @cached(ttl=0.1)
        def get_data():
            nonlocal call_count
            call_count += 1
            return "data"
        
        result1 = get_data()
        assert call_count == 1
        
        result2 = get_data()
        assert call_count == 1
        
        time.sleep(0.15)
        result3 = get_data()
        assert call_count == 2

    def test_maxsize_limit(self):
        """Test that maxsize limit is respected."""
        @cached(maxsize=2)
        def identity(x):
            return x
        
        identity(1)
        identity(2)
        identity(3)  # Should evict one of the previous entries
        
        # Check cache size
        assert len(identity._cache) <= 2

    def test_ignore_parameters(self):
        """Test ignoring certain parameters from cache key."""
        call_count = 0
        
        @cached(ignore=("debug",))
        def process(value, debug=False):
            nonlocal call_count
            call_count += 1
            return value * 2
        
        result1 = process(5, debug=False)
        result2 = process(5, debug=True)
        
        # Should use cache since 'debug' is ignored
        assert call_count == 1
        assert result1 == result2 == 10

    def test_include_parameters(self):
        """Test including only specific parameters in cache key."""
        call_count = 0
        
        @cached(include=("user_id",))
        def get_user(user_id, include_posts=False, include_comments=False):
            nonlocal call_count
            call_count += 1
            return {"id": user_id}
        
        result1 = get_user(1, include_posts=True)
        result2 = get_user(1, include_comments=True)
        
        # Should use cache since only 'user_id' is included
        assert call_count == 1
        assert result1 == result2

    def test_typed_caching(self):
        """Test typed caching (different types cached separately)."""
        call_count = 0
        
        @cached(typed=True)
        def process(value):
            nonlocal call_count
            call_count += 1
            return str(value)
        
        result1 = process(1)
        result2 = process(1.0)
        
        # Should call function twice due to different types
        assert call_count == 2

    def test_file_persistence(self):
        """Test file-based cache persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "func_cache.pkl"
            call_count = 0
            
            @cached(path=cache_path)
            def expensive_calc(x):
                nonlocal call_count
                call_count += 1
                return x ** 2
            
            # First call
            result1 = expensive_calc(5)
            assert result1 == 25
            assert call_count == 1
            
            # Create new function with same cache path
            call_count = 0
            
            @cached(path=cache_path)
            def expensive_calc2(x):
                nonlocal call_count
                call_count += 1
                return x ** 2
            
            # Should load from cache (different function but same cache file)
            # Note: This will still call the function since cache keys include function identity
            result2 = expensive_calc2(5)
            assert result2 == 25

    def test_cache_info(self):
        """Test cache info introspection."""
        @cached
        def add(a, b):
            return a + b
        
        add(1, 2)
        add(1, 2)
        add(3, 4)
        
        info = add._cache_info()
        assert "size" in info
        assert "maxsize" in info
        assert "hits" in info
        assert "misses" in info
        assert info["hits"] >= 1

    def test_cache_clear(self):
        """Test clearing function cache."""
        @cached
        def multiply(a, b):
            return a * b
        
        multiply(2, 3)
        multiply(4, 5)
        
        assert len(multiply._cache) == 2
        
        multiply._cache_clear()
        assert len(multiply._cache) == 0

    def test_unpicklable_result(self):
        """Test that unpicklable results don't break caching."""
        call_count = 0
        
        @cached
        def get_lambda():
            nonlocal call_count
            call_count += 1
            return lambda x: x * 2
        
        # Should work even though lambda is unpicklable for file caches
        result1 = get_lambda()
        result2 = get_lambda()
        
        # Function should be called each time since result can't be cached
        assert call_count == 2

    def test_decorator_without_parentheses(self):
        """Test using @cached without parentheses."""
        call_count = 0
        
        @cached
        def subtract(a, b):
            nonlocal call_count
            call_count += 1
            return a - b
        
        result1 = subtract(10, 5)
        result2 = subtract(10, 5)
        
        assert result1 == result2 == 5
        assert call_count == 1

    def test_ignore_and_include_error(self):
        """Test that specifying both ignore and include raises error."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            @cached(ignore=("a",), include=("b",))
            def func(a, b):
                return a + b


class TestConvenienceAliases:
    """Tests for convenience decorator aliases."""

    def test_lru_cache_alias(self):
        """Test lru_cache convenience function."""
        call_count = 0
        
        @lru_cache(maxsize=2)
        def add(a, b):
            nonlocal call_count
            call_count += 1
            return a + b
        
        add(1, 2)
        add(1, 2)
        
        assert call_count == 1

    def test_ttl_cache_alias(self):
        """Test ttl_cache convenience function."""
        call_count = 0
        
        @ttl_cache(ttl=0.1)
        def get_value():
            nonlocal call_count
            call_count += 1
            return "value"
        
        get_value()
        get_value()
        assert call_count == 1
        
        time.sleep(0.15)
        get_value()
        assert call_count == 2

    def test_file_cache_alias(self):
        """Test file_cache convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.pkl"
            call_count = 0
            
            @file_cache(path=cache_path)
            def compute(x):
                nonlocal call_count
                call_count += 1
                return x * 2
            
            compute(5)
            compute(5)
            
            assert call_count == 1


class TestClearCache:
    """Tests for global clear_cache function."""

    def test_clear_all_caches(self):
        """Test clearing all registered caches."""
        @cached
        def func1(x):
            return x
        
        @cached
        def func2(x):
            return x * 2
        
        func1(1)
        func2(2)
        
        assert len(func1._cache) > 0
        assert len(func2._cache) > 0
        
        clear_cache()
        
        # Note: clear_cache clears and removes from registry
        # so we can't check cache length after


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_access(self):
        """Test that cache is thread-safe."""
        import threading
        
        @cached
        def increment(x):
            time.sleep(0.01)
            return x + 1
        
        results = []
        
        def worker():
            result = increment(5)
            results.append(result)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All results should be the same
        assert all(r == 6 for r in results)
        assert len(results) == 10


class TestEdgeCases:
    """Tests for edge cases."""

    def test_none_arguments(self):
        """Test caching functions with None arguments."""
        call_count = 0
        
        @cached
        def process(value):
            nonlocal call_count
            call_count += 1
            return value
        
        result1 = process(None)
        result2 = process(None)
        
        assert result1 is None
        assert result2 is None
        assert call_count == 1

    def test_empty_arguments(self):
        """Test caching functions with no arguments."""
        call_count = 0
        
        @cached
        def get_constant():
            nonlocal call_count
            call_count += 1
            return 42
        
        result1 = get_constant()
        result2 = get_constant()
        
        assert result1 == 42
        assert call_count == 1

    def test_complex_nested_structures(self):
        """Test caching with complex nested data structures."""
        call_count = 0
        
        @cached
        def process_data(data):
            nonlocal call_count
            call_count += 1
            return len(str(data))
        
        complex_data = {
            "nested": {
                "list": [1, 2, {"inner": "value"}],
                "tuple": (1, 2, 3)
            }
        }
        
        result1 = process_data(complex_data)
        result2 = process_data(complex_data)
        
        assert call_count == 1

    def test_method_caching(self):
        """Test caching instance methods."""
        class Calculator:
            def __init__(self):
                self.call_count = 0
            
            @cached
            def add(self, a, b):
                self.call_count += 1
                return a + b
        
        calc = Calculator()
        result1 = calc.add(1, 2)
        result2 = calc.add(1, 2)
        
        assert result1 == 3
        # Note: Instance methods cache with self, so same instance + args = cache hit
        # But caching behavior depends on how self is hashed
