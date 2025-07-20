"""hammad._internal

Internal utilities"""

from typing import Any, Callable, List, Tuple, Union
import inspect
import ast
import hashlib

# pretty
from rich.traceback import install

install()

__all__ = ("create_getattr_importer",)


class GetAttrImporterError(Exception):
    """An error that occurs when the `create_getattr_importer` function
    fails to create a lazy loader function."""


class GetAttrImporterCache:
    """Minimal cache implementation for internal use only
    within the `create_getattr_importer` function."""

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


# NOTE:
# SINGLETON
GETATTR_IMPORTER_PARSE_CACHE = GetAttrImporterCache(maxsize=64)
"""Library-wide singleton instance providing caching for the 
`_parse_type_checking_imports` function."""


GETATTR_IMPORTER_TYPE_CHECKING_CACHE = {}
"""Cache for the `_parse_type_checking_imports` function."""


def _parse_type_checking_imports(source_code: str) -> dict[str, tuple[str, str]]:
    """Parses the TYPE_CHECKING imports from a source code file, to create
    a dictionary of local names to (module_path, original_name) tuples.

    This is used to create the mapping used within the `_create_getattr_importer_from_import_dict`
    function.

    Args:
        source_code : The source code to parse

    Returns:
        A dictionary mapping local names to (module_path, original_name) tuples
    """

    @GETATTR_IMPORTER_PARSE_CACHE.cached_call
    def _exec(source_code: str) -> dict[str, tuple[str, str]]:
        tree = ast.parse(source_code)
        imports = {}

        # Walk through the AST and find TYPE_CHECKING blocks
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
                            # Only add '.' prefix for relative imports
                            # If stmt.level > 0, it's already a relative import
                            # If stmt.level == 0 and module doesn't start with '.', it's absolute
                            if stmt.level > 0:
                                # Already relative import
                                module_path = "." * stmt.level + (stmt.module or "")
                            elif stmt.module.startswith("."):
                                # Explicit relative import
                                module_path = stmt.module
                            elif any(
                                stmt.module.startswith(name)
                                for name in ["litellm", "openai", "instructor", "httpx"]
                            ):
                                # Known absolute third-party imports
                                module_path = stmt.module
                            else:
                                # Default to relative import for internal modules
                                module_path = f".{stmt.module}"

                            for alias in stmt.names:
                                original_name = alias.name
                                local_name = alias.asname or original_name
                                imports[local_name] = (module_path, original_name)

        return imports

    return _exec(source_code)


def _create_getattr_importer_from_import_dict(
    imports_dict: dict[str, tuple[str, str]],
    package: str,
    all_attrs: Union[Tuple[str, ...], List[str]],
) -> Callable[[str], Any]:
    """Creates a lazy loader function for the `__getattr__` method
    within `__init__.py` modules in Python packages.

    Args:
        imports_dict : Dictionary mapping attribute names to (module_path, original_name) tuples
        package : The package name for import_module
        all_attrs : List of all valid attributes for this module

    Returns:
        A __getattr__ function that lazily imports modules
    """
    from importlib import import_module

    cache = {}

    def __getattr__(name: str) -> Any:
        if name in cache:
            return cache[name]

        if name in imports_dict:
            module_path, original_name = imports_dict[name]
            module = import_module(module_path, package)
            result = getattr(module, original_name)
            cache[name] = result
            return result

        # Try to import as a submodule
        try:
            module_path = f".{name}"
            module = import_module(module_path, package)
            cache[name] = module
            return module
        except ImportError:
            pass

        raise GetAttrImporterError(f"module '{package}' has no attribute '{name}'")

    return __getattr__


def create_getattr_importer(
    all: Union[Tuple[str, ...], List[str]],
) -> Callable[[str], Any]:
    """Loader used internally within the `hammad` package to create lazy
    loaders within `__init__.py` modules using the `TYPE_CHECKING` and
    `all` source code within files.

    This function is meant to be set as the `__getattr__` method / var
    within modules to allow for direct lazy loading of attributes.

    Example:

        ```
        # Create a module that contains some imports and TYPE_CHECKING
        from typing import TYPE_CHECKING
        from hammad.performance.imports import create_getattr_importer

        if TYPE_CHECKING:
            from functools import wraps

        all = ("wraps")

        __getattr__ = create_getattr_importer(all)

        # Now, when you import this module, the `wraps` attribute will be
        # lazily loaded when it is first accessed.
        ```

    Args:
        all : The `all` tuple from the calling module

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
    cache_key = (filename, tuple(all))
    if cache_key in GETATTR_IMPORTER_TYPE_CHECKING_CACHE:
        return GETATTR_IMPORTER_TYPE_CHECKING_CACHE[cache_key]

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
    filtered_map = {name: path for name, path in imports_map.items() if name in all}

    loader = _create_getattr_importer_from_import_dict(filtered_map, package, all)
    GETATTR_IMPORTER_TYPE_CHECKING_CACHE[cache_key] = loader
    return loader
