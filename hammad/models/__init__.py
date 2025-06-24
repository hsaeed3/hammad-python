"""hammad.models

Contains the `BasedModel` and `basefield` system, an 'opinionated' Pydantic model clone
using `msgspec` for faster serialization and deserialization as well as providing a few other
extended functionality such as model conversion, turning fields into models, and more."""

from .basedfields import BasedFieldInfo, BasedField, basedfield
from .basedmodel import BasedModel
from .fn import (
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
    "BasedFieldInfo",
    "BasedField",
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