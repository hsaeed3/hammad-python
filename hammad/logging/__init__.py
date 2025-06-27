"""hammad.logging"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import create_logger, create_logger_level
    from .decorators import trace_function, trace_cls, trace


__all__ = (
    "create_logger",
    "create_logger_level",
    "trace_function",
    "trace_cls",
    "trace",
)

def __getattr__(name: str):
    """Get an attribute from the logging module."""
    from importlib import import_module

    # Map attributes to their respective modules
    module_map = {
        "create_logger": "logger",
        "create_logger_level": "logger", 
        "trace_function": "decorators",
        "trace_cls": "decorators",
        "trace": "decorators",
    }
    
    if name in module_map:
        module_name = module_map[name]
        if not hasattr(__getattr__, f"_{module_name}_module"):
            setattr(__getattr__, f"_{module_name}_module", import_module(f".{module_name}", __package__))
        module = getattr(__getattr__, f"_{module_name}_module")
        return getattr(module, name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__() -> list[str]:
    """Get the attributes of the logging module."""
    return list(__all__)