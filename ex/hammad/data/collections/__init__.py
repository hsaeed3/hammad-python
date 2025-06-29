"""hammad.data.collections"""

from typing import TYPE_CHECKING
from ...based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .base_collection import BaseCollection
    from .searchable_collection import SearchableCollection
    from .vector_collection import VectorCollection
    from .collection import (
        create_collection,
        VectorCollectionSettings,
        SearchableCollectionSettings,
    )


__all__ = (
    "BaseCollection",
    "SearchableCollection",
    "VectorCollection",
    "create_collection",
    "VectorCollectionSettings",
    "SearchableCollectionSettings",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.collections module."""
    return list(__all__)
