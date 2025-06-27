"""hammad.pydantic.models"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .arbitrary_model import ArbitraryModel
    from .cacheable_model import CacheableModel
    from .fast_model import FastModel
    from .function_model import FunctionModel
    from .subscriptable_model import SubscriptableModel


__all__ = (
    "ArbitraryModel",
    "CacheableModel",
    "FastModel",
    "FunctionModel",
    "SubscriptableModel",
)


def __getattr__(name: str):
    """Get an attribute from the models module."""
    from importlib import import_module

    # Map of attribute names to their respective modules
    module_map = {
        "ArbitraryModel": ".arbitrary_model",
        "CacheableModel": ".cacheable_model",
        "FastModel": ".fast_model",
        "FunctionModel": ".function_model",
        "SubscriptableModel": ".subscriptable_model",
    }

    if name in module_map:
        module = import_module(module_map[name], __package__)
        return getattr(module, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Get the attributes of the models module."""
    return list(__all__)
