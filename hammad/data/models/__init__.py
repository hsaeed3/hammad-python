"""hammad.data.models

Contains **BOTH** resources contains predefined models or base class like
models, as well as modules & utilities specifically for various interfaces
of models such as `pydantic`."""

from typing import TYPE_CHECKING
from ...performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .base import (
        Model,
        field,
        validator,
        is_field,
        is_model,
        model_settings
    )
    from .pydantic import (
        convert_to_pydantic_model,
        convert_to_pydantic_field
    )


__all__ = (
    # hammad.models.base
    "Model",
    "field",
    "validator",
    "is_field",
    "is_model",
    "model_settings",

    # hammad.models.pydantic
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)