"""hammad.data.models.pydantic.models"""

from typing import TYPE_CHECKING
from .....performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .arbitrary_model import ArbitraryModel
    from .cacheable_model import CacheableModel
    from .fast_model import FastModel
    from .function_model import FunctionModel
    from .subscriptable_model import SubscriptableModel


__all__ = (
    "ArbitraryModel",
    "CacheableModel",
    "FastModel",
    "FunctionModel",
    "SubscriptableModel",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the models module."""
    return list(__all__)
