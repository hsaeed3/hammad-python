"""hammad.core.models

Contains **BOTH** resources contains predefined models or base class like
models, as well as modules & utilities specifically for various interfaces
of models such as `pydantic`."""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer

if TYPE_CHECKING:
    from .model import (
        Model,
        model_settings,
    )
    from .fields import (
        Field,
        FieldInfo,
        field,
        int_field,
        str_field,
        list_field,
        float_field,
    )
    from .utils import (
        validator,
        is_field,
        is_model,
    )


__all__ = (
    # ham.core.models.model
    "Model",
    "model_settings",
    # ham.core.models.fields
    "Field",
    "FieldInfo",
    "field",
    "int_field",
    "str_field",
    "list_field",
    "float_field",
    # ham.core.models.utils
    "validator",
    "is_field",
    "is_model",
    "model_settings",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
