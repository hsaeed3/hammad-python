"""hammad.data.models

Contains **BOTH** resources contains predefined models or base class like
models, as well as modules & utilities specifically for various interfaces
of models such as `pydantic`."""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .model import (
        Model,
        model_settings,
    )
    from .fields import field
    from .utils import (
        validator,
        is_field,
        is_model,
    )
    from .extensions.pydantic.converters import (
        convert_to_pydantic_model,
        convert_to_pydantic_field,
        is_pydantic_model_class,
    )


__all__ = (
    # hammad.lib.data.models.model
    "Model",
    "model_settings",
    # hammad.lib.data.models.fields
    "field",
    # hammad.lib.data.models.utils
    "validator",
    "is_field",
    "is_model",
    "model_settings",
    # hammad.lib.data.models.extensions.pydantic.converters
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "is_pydantic_model_class",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
