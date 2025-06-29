"""hammad.core.base

Contains resources that build the `BasedModel` & `basedfield` components.
This system is built to 'mock' a Pydantic Model, using `msgspec` for faster
serialization as well as extended functionality through the model."""

from typing import TYPE_CHECKING
from .utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .fields import (
        basedfield,
        str_basedfield,
        int_basedfield,
        float_basedfield,
        list_basedfield,
        BasedFieldInfo,
        BasedField,
    )
    from .model import BasedModel
    from .utils import (
        create_basedmodel,
        get_field_info,
        is_basedfield,
        is_basedmodel,
        based_validator,
    )


__all__ = (
    "basedfield",
    "str_basedfield",
    "int_basedfield",
    "float_basedfield",
    "list_basedfield",
    "BasedFieldInfo",
    "BasedField",
    "BasedModel",
    "create_basedmodel",
    "get_field_info",
    "is_basedfield",
    "is_basedmodel",
    "based_validator",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the based module."""
    return list(__all__)
