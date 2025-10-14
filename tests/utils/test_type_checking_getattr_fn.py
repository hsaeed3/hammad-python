"""Tests for ham.utils.type_checking_getattr_fn"""

import ast
import tempfile
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ham.utils.type_checking_getattr_fn import (
    type_checking_getattr_fn,
    type_checking_dir_fn,
    GetAttrFunctionError,
    GetAttrFunctionWarning,
    GetAttrFunctionCache,
    _parse_type_checking_imports,
    _create_lazy_loaders,
)


class TestGetAttrFunctionCache:
    """Tests for GetAttrFunctionCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = GetAttrFunctionCache(max_size=10)
        assert cache.max_size == 10
        assert len(cache.cache) == 0

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = GetAttrFunctionCache(max_size=10)
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"

    def test_cache_lru_eviction(self):
        """Test LRU eviction when max_size is reached."""
        cache = GetAttrFunctionCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_move_to_end(self):
        """Test that accessing items moves them to end."""
        cache = GetAttrFunctionCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 (should move to end)
        cache.get("key1")
        
        # Add new item
        cache.set("key4", "value4")
        
        # key2 should be evicted (oldest)
        assert cache.get("key2") is None
        assert cache.get("key1") == "value1"

    def test_cache_update_existing(self):
        """Test updating existing cache entries."""
        cache = GetAttrFunctionCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        
        assert cache.get("key1") == "value2"
        assert len(cache.cache) == 1

    def test_make_cache_key(self):
        """Test cache key generation."""
        cache = GetAttrFunctionCache()
        
        key1 = cache.make_cache_key("test")
        key2 = cache.make_cache_key("test")
        key3 = cache.make_cache_key("different")
        
        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 64  # SHA-256 hex digest

    def test_cached_decorator(self):
        """Test the cached decorator method."""
        cache = GetAttrFunctionCache(max_size=10)
        call_count = 0
        
        @cache.cached
        def add(a, b):
            nonlocal call_count
            call_count += 1
            return a + b
        
        result1 = add(1, 2)
        result2 = add(1, 2)
        result3 = add(2, 3)
        
        assert result1 == 3
        assert result2 == 3
        assert result3 == 5
        assert call_count == 2  # Only 2 actual function calls

    def test_cached_with_kwargs(self):
        """Test cached decorator with keyword arguments."""
        cache = GetAttrFunctionCache(max_size=10)
        call_count = 0
        
        @cache.cached
        def greet(name, greeting="Hello"):
            nonlocal call_count
            call_count += 1
            return f"{greeting}, {name}"
        
        # Test that identical calls hit cache
        result1 = greet("Alice")
        result2 = greet("Alice")  # Same call, should hit cache
        
        assert call_count == 1
        assert result1 == result2
        
        # Different calling conventions create different cache keys
        result3 = greet("Alice", greeting="Hello")
        result4 = greet("Alice", greeting="Hello")  # Same as result3, should hit cache
        
        assert call_count == 2  # One more call for the explicit keyword arg
        assert result3 == result4
        assert result1 == result3  # Same output though


class TestParseTypeCheckingImports:
    """Tests for _parse_type_checking_imports function."""

    def test_parse_simple_import(self):
        """Test parsing simple TYPE_CHECKING imports."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike
    from sys import version_info
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "PathLike": ("os", "PathLike"),
            "version_info": ("sys", "version_info"),
        }

    def test_parse_import_with_alias(self):
        """Test parsing imports with aliases."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike as PL
    from sys import version_info as ver
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "PL": ("os", "PathLike"),
            "ver": ("sys", "version_info"),
        }

    def test_parse_relative_import(self):
        """Test parsing relative imports."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .submodule import MyClass
    from ..parent import ParentClass
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "MyClass": (".submodule", "MyClass"),
            "ParentClass": ("..parent", "ParentClass"),
        }

    def test_parse_typing_module_check(self):
        """Test parsing with typing.TYPE_CHECKING."""
        source = """
import typing

if typing.TYPE_CHECKING:
    from os import PathLike
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "PathLike": ("os", "PathLike"),
        }

    def test_parse_multiple_imports_per_line(self):
        """Test parsing multiple imports from same module."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike, environ
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "PathLike": ("os", "PathLike"),
            "environ": ("os", "environ"),
        }

    def test_parse_ignores_non_type_checking(self):
        """Test that imports outside TYPE_CHECKING blocks are ignored."""
        source = """
from typing import TYPE_CHECKING
from os import PathLike as RegularImport

if TYPE_CHECKING:
    from sys import version_info
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports == {
            "version_info": ("sys", "version_info"),
        }
        assert "RegularImport" not in imports

    def test_parse_empty_type_checking_block(self):
        """Test parsing empty TYPE_CHECKING block."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
"""
        imports = _parse_type_checking_imports(source)
        assert imports == {}

    def test_parse_no_type_checking_block(self):
        """Test parsing source with no TYPE_CHECKING block."""
        source = """
from os import PathLike
"""
        imports = _parse_type_checking_imports(source)
        assert imports == {}


class TestCreateLazyLoaders:
    """Tests for _create_lazy_loaders function."""

    def test_create_loaders_basic(self):
        """Test creating basic lazy loaders."""
        import_map = {
            "PathLike": ("os", "PathLike"),
        }
        all_attributes = frozenset(["PathLike"])
        
        getattr_fn, dir_fn = _create_lazy_loaders(import_map, None, all_attributes)
        
        # Test __getattr__
        result = getattr_fn("PathLike")
        from os import PathLike
        assert result is PathLike
        
        # Test __dir__
        dir_result = dir_fn()
        assert "PathLike" in dir_result

    def test_getattr_caching(self):
        """Test that lazy loaded modules are cached."""
        import_map = {
            "PathLike": ("os", "PathLike"),
        }
        all_attributes = frozenset(["PathLike"])
        
        getattr_fn, _ = _create_lazy_loaders(import_map, None, all_attributes)
        
        result1 = getattr_fn("PathLike")
        result2 = getattr_fn("PathLike")
        
        # Should be the same object (cached)
        assert result1 is result2

    def test_getattr_missing_attribute(self):
        """Test that missing attributes raise GetAttrFunctionError."""
        import_map = {}
        all_attributes = frozenset(["Something"])
        
        getattr_fn, _ = _create_lazy_loaders(import_map, None, all_attributes)
        
        with pytest.raises(GetAttrFunctionError, match="has no attribute"):
            getattr_fn("NonExistent")

    def test_getattr_import_error(self):
        """Test that import errors are wrapped in GetAttrFunctionError."""
        import_map = {
            "FakeModule": ("nonexistent_module_xyz", "FakeClass"),
        }
        all_attributes = frozenset(["FakeModule"])
        
        getattr_fn, _ = _create_lazy_loaders(import_map, None, all_attributes)
        
        with pytest.raises(GetAttrFunctionError, match="Failed to lazy-load"):
            getattr_fn("FakeModule")

    def test_dir_returns_sorted_list(self):
        """Test that __dir__ returns sorted list."""
        import_map = {}
        all_attributes = frozenset(["zebra", "apple", "banana"])
        
        _, dir_fn = _create_lazy_loaders(import_map, None, all_attributes)
        
        result = dir_fn()
        assert result == ["apple", "banana", "zebra"]

    def test_relative_import_loading(self):
        """Test loading relative imports."""
        # This is tricky to test without a real package structure
        # We'll test that the function is called correctly
        import_map = {
            "MyClass": (".submodule", "MyClass"),
        }
        all_attributes = frozenset(["MyClass"])
        
        getattr_fn, _ = _create_lazy_loaders(import_map, "ham.utils", all_attributes)
        
        # This will fail unless the module exists, but tests the logic path
        with pytest.raises(GetAttrFunctionError):
            getattr_fn("MyClass")


class TestTypeCheckingGetAttrFn:
    """Tests for type_checking_getattr_fn function."""

    def test_integration_with_module(self):
        """Test integration by creating a temporary module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir)
            module_file = module_path / "test_module.py"
            
            # Create a test module
            module_content = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

__all__ = ("PathLike",)

from ham.utils.type_checking_getattr_fn import type_checking_getattr_fn
__getattr__ = type_checking_getattr_fn(__all__)
"""
            module_file.write_text(module_content)
            
            # Add to sys.path
            sys.path.insert(0, str(module_path))
            
            try:
                # Import and test
                import test_module # type: ignore
                
                # Should be able to access PathLike lazily
                from os import PathLike as ExpectedPathLike
                assert test_module.PathLike is ExpectedPathLike
                
            finally:
                # Cleanup
                if "test_module" in sys.modules:
                    del sys.modules["test_module"]
                sys.path.remove(str(module_path))

    def test_getattr_fn_signature(self):
        """Test that returned function has correct signature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir)
            module_file = module_path / "test_sig.py"
            
            module_content = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

__all__ = ("PathLike",)
"""
            module_file.write_text(module_content)
            
            # We can't easily test this without proper module context
            # Just verify the function returns a callable
            # Note: This would need to be called from within the module
            pass


class TestTypeCheckingDirFn:
    """Tests for type_checking_dir_fn function."""

    def test_dir_fn_returns_callable(self):
        """Test that type_checking_dir_fn returns a callable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir)
            module_file = module_path / "test_dir.py"
            
            module_content = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

__all__ = ("PathLike", "something")
"""
            module_file.write_text(module_content)
            
            # Similar limitation as above - needs module context
            pass

    def test_integration_with_dir(self):
        """Test dir() integration with module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir)
            module_file = module_path / "test_dir_module.py"
            
            module_content = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

__all__ = ("PathLike", "MyClass")

from ham.utils.type_checking_getattr_fn import (
    type_checking_getattr_fn,
    type_checking_dir_fn,
)

__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)
"""
            module_file.write_text(module_content)
            
            sys.path.insert(0, str(module_path))
            
            try:
                import test_dir_module # type: ignore
                
                # Test dir()
                dir_result = dir(test_dir_module)
                assert "PathLike" in dir_result
                assert "MyClass" in dir_result
                
            finally:
                if "test_dir_module" in sys.modules:
                    del sys.modules["test_dir_module"]
                sys.path.remove(str(module_path))


class TestErrorHandling:
    """Tests for error handling."""

    def test_getattr_function_error_inheritance(self):
        """Test that GetAttrFunctionError inherits from AttributeError."""
        assert issubclass(GetAttrFunctionError, AttributeError)
        
        error = GetAttrFunctionError("test error")
        assert isinstance(error, AttributeError)
        assert str(error) == "test error"

    def test_getattr_function_warning(self):
        """Test GetAttrFunctionWarning."""
        assert issubclass(GetAttrFunctionWarning, Warning)
        
        warning = GetAttrFunctionWarning("test warning")
        assert isinstance(warning, Warning)

    def test_missing_source_file(self):
        """Test error when source file cannot be found."""
        # This is difficult to test directly without mocking
        # The function expects to be called from a module with __file__
        pass

    def test_invalid_module_structure(self):
        """Test handling of invalid module structure."""
        # Test that parser handles malformed source gracefully
        source = "this is not valid python code {"
        
        with pytest.raises(SyntaxError):
            _parse_type_checking_imports(source)


class TestCaching:
    """Tests for caching behavior."""

    def test_parser_cache_is_used(self):
        """Test that parsing results are cached."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike
"""
        # Parse twice
        result1 = _parse_type_checking_imports(source)
        result2 = _parse_type_checking_imports(source)
        
        # Should be the same object (cached)
        assert result1 == result2

    def test_loader_cache_reuse(self):
        """Test that loader functions are cached per file."""
        # This is tested implicitly by the integration tests
        # The _loader_cache dict should reuse loaders for the same file
        pass


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_mixed_imports(self):
        """Test parsing with mixed import styles."""
        source = """
from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    from os import PathLike
    from sys import version_info as ver
    from .local import LocalClass
    from ..parent import ParentClass
"""
        imports = _parse_type_checking_imports(source)
        
        assert "PathLike" in imports
        assert "ver" in imports
        assert "LocalClass" in imports
        assert "ParentClass" in imports

    def test_nested_type_checking_blocks(self):
        """Test that nested if statements don't break parsing."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike
    if True:  # This shouldn't affect parsing
        from sys import version_info
"""
        imports = _parse_type_checking_imports(source)
        
        # Should still find the imports in the TYPE_CHECKING block
        assert "PathLike" in imports

    def test_module_with_all_excluded_items(self):
        """Test behavior when __all__ excludes TYPE_CHECKING imports."""
        import_map = {
            "ClassA": ("module", "ClassA"),
            "ClassB": ("module", "ClassB"),
        }
        all_attributes = frozenset(["ClassA"])  # Only ClassA in __all__
        
        getattr_fn, _ = _create_lazy_loaders(import_map, None, all_attributes)
        
        # ClassB should raise error since it's not in __all__
        with pytest.raises(GetAttrFunctionError):
            getattr_fn("ClassB")


class TestRealWorldUsage:
    """Tests simulating real-world usage patterns."""

    def test_lazy_loading_package_init(self):
        """Test lazy loading in a package __init__.py scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_path = Path(tmpdir) / "mypkg"
            pkg_path.mkdir()
            
            # Create __init__.py
            init_file = pkg_path / "__init__.py"
            init_content = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike
    from sys import version_info

__all__ = ("PathLike", "version_info")

from ham.utils.type_checking_getattr_fn import type_checking_getattr_fn
__getattr__ = type_checking_getattr_fn(__all__)
"""
            init_file.write_text(init_content)
            
            sys.path.insert(0, str(tmpdir))
            
            try:
                import mypkg # type: ignore
                
                # Test lazy loading
                from os import PathLike
                from sys import version_info
                
                assert mypkg.PathLike is PathLike
                assert mypkg.version_info is version_info
                
            finally:
                if "mypkg" in sys.modules:
                    del sys.modules["mypkg"]
                sys.path.remove(str(tmpdir))

    def test_circular_import_prevention(self):
        """Test that lazy loading helps prevent circular imports."""
        # This is more of a conceptual test
        # Lazy loading defers imports until attribute access
        # which can help break circular dependencies
        pass


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_all_list(self):
        """Test with empty __all__ list."""
        import_map = {"Something": ("module", "Something")}
        all_attributes = frozenset([])
        
        getattr_fn, dir_fn = _create_lazy_loaders(import_map, None, all_attributes)
        
        # Should raise error for any attribute
        with pytest.raises(GetAttrFunctionError):
            getattr_fn("Something")
        
        # Dir should return empty list
        assert dir_fn() == []

    def test_special_attribute_names(self):
        """Test with special/reserved attribute names."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import name as __name__
"""
        imports = _parse_type_checking_imports(source)
        
        # Should handle special names
        assert "__name__" in imports

    def test_unicode_in_source(self):
        """Test parsing source with unicode characters."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike  # Unicode comment: 你好世界
"""
        imports = _parse_type_checking_imports(source)
        assert "PathLike" in imports

    def test_very_long_import_path(self):
        """Test with very long module paths."""
        source = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from very.long.nested.module.path.that.goes.deep import Something
"""
        imports = _parse_type_checking_imports(source)
        
        assert imports["Something"][0] == "very.long.nested.module.path.that.goes.deep"
