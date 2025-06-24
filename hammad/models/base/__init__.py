"""hammad.models.base

Contains resources that build the `BasedModel` & `basedfield` components.
This system is built to 'mock' a Pydantic Model, using `msgspec` for faster
serialization as well as extended functionality through the model."""

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
