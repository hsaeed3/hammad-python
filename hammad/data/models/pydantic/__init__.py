"""hammad.models.pydantic

Contains both models and pydantic **specific** utiltiies / resources
meant for general case usage."""

from typing import TYPE_CHECKING
from ....performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .models import (
        ArbitraryModel,
        CacheableModel,
        FastModel,
        FunctionModel,
        SubscriptableModel,
    )
    from .converters import (
        convert_to_pydantic_model,
        convert_to_pydantic_field,
        convert_dataclass_to_pydantic_model,
        convert_dict_to_pydantic_model,
        convert_function_to_pydantic_model,
        convert_sequence_to_pydantic_model,
        convert_type_to_pydantic_model,
        create_confirmation_pydantic_model,
        create_selection_pydantic_model,
    )


__all__ = (
    # hammad.models.pydantic.models
    "ArbitraryModel",
    "CacheableModel",
    "FastModel",
    "FunctionModel",
    "SubscriptableModel",
    # hammad.models.pydantic.converters
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "convert_dataclass_to_pydantic_model",
    "convert_dict_to_pydantic_model",
    "convert_function_to_pydantic_model",
    "convert_sequence_to_pydantic_model",
    "convert_type_to_pydantic_model",
    "create_confirmation_pydantic_model",
    "create_selection_pydantic_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the models module."""
    return list(__all__)
