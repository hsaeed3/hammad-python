"""hammad.data.collections"""

from typing import TYPE_CHECKING
from ..._core._utils._import_utils import _auto_create_getattr_loader

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


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.collections module."""
    return list(__all__)
