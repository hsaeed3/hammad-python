"""hammad.data"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .collections import (
        Collection,
        BaseCollection,
        VectorCollection,
        VectorCollectionSettings,
        SearchableCollection,
        SearchableCollectionSettings,
        create_collection,
    )
    from .databases import Database, create_database


__all__ = (
    # hammad.data.collections
    "Collection",
    "BaseCollection",
    "VectorCollection",
    "VectorCollectionSettings",
    "SearchableCollection",
    "SearchableCollectionSettings",
    "create_collection",
    # hammad.data.databases
    "Database",
    "create_database",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data module."""
    return list(__all__)
