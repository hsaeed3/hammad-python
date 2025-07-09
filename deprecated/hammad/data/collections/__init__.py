"""hammad.data.collections"""

from typing import TYPE_CHECKING
from ...performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .base_collection import BaseCollection
    from .searchable_collection import SearchableCollection
    from .vector_collection import VectorCollection
    from .collection import (
        create_collection,
        VectorCollectionSettings,
        SearchableCollectionSettings,
        Collection,
    )


__all__ = (
    "BaseCollection",
    "SearchableCollection",
    "VectorCollection",
    "create_collection",
    "VectorCollectionSettings",
    "SearchableCollectionSettings",
    "Collection",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.collections module."""
    return list(__all__)
