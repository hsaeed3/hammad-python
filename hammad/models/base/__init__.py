"""hammad.models.base

Contains resources that build the `Model` & `field` components.
This system is built to 'mock' a Pydantic Model, using `msgspec` for faster
serialization as well as extended functionality through the model."""

from typing import TYPE_CHECKING
from ..._internal import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .model import Model, model_settings
    from .fields import (
        field,
    )
    from .utils import (
        create_model,
        validator,
        is_field,
        is_model,
        get_field_info
    )

__all__ = (
    "Model",
    "model_settings",
    "field",
    "create_model",
    "validator",
    "is_field",
    "is_model",
    "get_field_info",
)

__getattr__ = _auto_create_getattr_loader(__all__)

def __dir__() -> list[str]:
    return list(__all__)
