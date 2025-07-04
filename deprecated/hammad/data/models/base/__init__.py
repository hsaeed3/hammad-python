"""hammad.models.base

Contains the `Model` and `field` system along with an assortment
of various utilities for interacting and managing these objects.
"""

from typing import TYPE_CHECKING
from ....performance.imports import create_getattr_importer

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

__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
