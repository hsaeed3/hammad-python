"""hammad.models

Contains the `Model` and `field` system along with an assortment
of various utilities for interacting and managing these objects.

NOTE: If you are looking for the location of 'opnionated' or defined
model-like objects, please use `hammad.types`.
"""

from typing import TYPE_CHECKING
from .._common._loader import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .model import Model, model_settings
    from .fields import field, Field, FieldInfo
    from .utils import create_model, validator, is_field, is_model, get_field_info

__all__ = (
    # hammad.models.model
    "Model",
    "model_settings",
    # hammad.models.fields
    "field",
    "Field",
    "FieldInfo",
    # hammad.models.utils
    "create_model",
    "validator",
    "is_field",
    "is_model",
    "get_field_info",
)

__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
