"""hammad.core.base

Contains resources that build the `BasedModel` & `basedfield` components.
This system is built to 'mock' a Pydantic Model, using `msgspec` for faster
serialization as well as extended functionality through the model."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fields import basedfield
    from .model import BasedModel
    from .utils import (
        create_basedmodel,
        get_field_info,
        is_basedfield,
        is_basedmodel,
        basedvalidator,
        str_basedfield,
        int_basedfield,
        float_basedfield,
        list_basedfield,
    )

__all__ = (
    "BasedModel",
    "basedfield",
    "create_basedmodel",
    "get_field_info",
    "is_basedfield",
    "is_basedmodel",
    "basedvalidator",
    "str_basedfield",
    "int_basedfield",
    "float_basedfield",
    "list_basedfield",
)


def __getattr__(name: str):
    """Get an attribute from the based module."""
    from importlib import import_module

    # Map attribute names to their respective modules
    module_map = {
        "BasedModel": "model",
        "basedfield": "fields",
        "BasedFieldInfo": "fields",
        "BasedField": "fields",
        "create_basedmodel": "utils",
        "get_field_info": "utils",
        "is_basedfield": "utils",
        "is_basedmodel": "utils",
        "basedvalidator": "utils",
        "str_basedfield": "utils",
        "int_basedfield": "utils",
        "float_basedfield": "utils",
        "list_basedfield": "utils",
    }

    if name not in module_map:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_name = module_map[name]
    module = import_module(f".{module_name}", __package__)
    return getattr(module, name)


def __dir__() -> list[str]:
    """Get the attributes of the based module."""
    return list(__all__)
