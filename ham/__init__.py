"""`hammad-python`"""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)


try:
    from ham.core._internal import set_debug, set_verbose
except ImportError:
    # Fallback to relative import
    from .core._internal import set_debug, set_verbose # type: ignore


__all__ = ["set_debug", "set_verbose"]
