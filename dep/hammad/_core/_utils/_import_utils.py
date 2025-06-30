"""hammad._core._utils._import_utils"""

from typing import Any, Callable
import inspect
import ast
import hashlib

__all__ = ("_auto_create_getattr_loader",)


class _ModuleCache:
    """Minimal cache implementation for internal use only."""

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._cache: dict[str, Any] = {}

    def _make_key(self, data: str) -> str:
        """Create a simple hash key from string data."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with basic LRU eviction."""
        if len(self._cache) >= self.maxsize and key not in self._cache:
            # Simple eviction: remove oldest (first) item
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = value

    def cached_call(self, func: Callable[[str], Any]) -> Callable[[str], Any]:
        """Decorator to cache function calls."""

        def wrapper(arg: str) -> Any:
            key = self._make_key(arg)
            result = self.get(key)
            if result is None:
                result = func(arg)
                self.set(key, result)
            return result

        return wrapper


# Global cache instance for parse function
_parse_cache = _ModuleCache(maxsize=64)


def _create_getattr_loader(
    imports_dict: dict[str, tuple[str, str]], package: str
) -> Callable[[str], Any]:
    """Create a lazy loader function for __getattr__.

    Args:
        imports_dict: Dictionary mapping attribute names to (module_path, original_name) tuples
        package: The package name for import_module

    Returns:
        A __getattr__ function that lazily imports modules
    """
    from importlib import import_module

    _cache = {}

    def __getattr__(name: str) -> Any:
        if name in _cache:
            return _cache[name]

        if name in imports_dict:
            module_path, original_name = imports_dict[name]
            module = import_module(module_path, package)
            result = getattr(module, original_name)
            _cache[name] = result
            return result
        raise AttributeError(f"module '{package}' has no attribute '{name}'")

    return __getattr__


_type_checking_cache = {}


def _auto_create_getattr_loader(all_exports: tuple[str, ...]) -> Callable[[str], Any]:
    """Automatically create a lazy loader by inspecting the calling module.

    This function inspects the calling module's source code to extract
    TYPE_CHECKING imports and automatically builds the import map.

    Args:
        all_exports: The __all__ tuple from the calling module

    Returns:
        A __getattr__ function that lazily imports modules
    """
    # Get the calling module's frame
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        raise RuntimeError("Cannot determine calling module")

    calling_frame = frame.f_back
    module_name = calling_frame.f_globals.get("__name__", "")
    package = calling_frame.f_globals.get("__package__", "")
    filename = calling_frame.f_globals.get("__file__", "")

    # Check cache first
    cache_key = (filename, tuple(all_exports))
    if cache_key in _type_checking_cache:
        return _type_checking_cache[cache_key]

    # Read the source file
    try:
        with open(filename, "r") as f:
            source_code = f.read()
    except (IOError, OSError):
        # Fallback: try to get source from the module
        import sys

        module = sys.modules.get(module_name)
        if module:
            source_code = inspect.getsource(module)
        else:
            raise RuntimeError(f"Cannot read source for module {module_name}")

    # Parse the source to extract TYPE_CHECKING imports
    imports_map = _parse_type_checking_imports(source_code)

    # Filter to only include exports that are in __all__
    filtered_map = {
        name: path for name, path in imports_map.items() if name in all_exports
    }

    loader = _create_getattr_loader(filtered_map, package)
    _type_checking_cache[cache_key] = loader
    return loader


def _parse_type_checking_imports(source_code: str) -> dict[str, tuple[str, str]]:
    """Parse TYPE_CHECKING imports from source code to build import map.

    Args:
        source_code: The source code containing TYPE_CHECKING imports

    Returns:
        Dictionary mapping local names to (module_path, original_name) tuples
    """

    @_parse_cache.cached_call
    def _exec(source_code: str) -> dict[str, tuple[str, str]]:
        tree = ast.parse(source_code)
        imports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check if this is a TYPE_CHECKING block
                is_type_checking = False

                if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                    is_type_checking = True
                elif isinstance(node.test, ast.Attribute):
                    if (
                        isinstance(node.test.value, ast.Name)
                        and node.test.value.id == "typing"
                        and node.test.attr == "TYPE_CHECKING"
                    ):
                        is_type_checking = True

                if is_type_checking:
                    # Process imports in this block
                    for stmt in node.body:
                        if isinstance(stmt, ast.ImportFrom) and stmt.module:
                            module_path = f".{stmt.module}"
                            for alias in stmt.names:
                                original_name = alias.name
                                local_name = alias.asname or original_name
                                imports[local_name] = (module_path, original_name)

        return imports

    return _exec(source_code)
