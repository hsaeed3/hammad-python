"""hammad.pydantic

Contains both models and pydantic **specific** utiltiies / resources
meant for general case usage."""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .converters import (
        convert_to_pydantic_model,
        convert_to_pydantic_field,
        create_confirmation_pydantic_model,
        create_selection_pydantic_model,
    )
    from .models import (
        FastModel,
        FunctionModel,
        ArbitraryModel,
        CacheableModel,
        SubscriptableModel,
    )


__all__ = (
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "create_confirmation_pydantic_model",
    "create_selection_pydantic_model",
    "FastModel",
    "FunctionModel",
    "ArbitraryModel",
    "CacheableModel",
    "SubscriptableModel",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the pydantic module."""
    return list(__all__)
