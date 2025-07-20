"""ham.data.collections"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from .collection import (
        Collection,
        create_collection,
        CollectionType,
    )

    from .indexes import (
        TantivyCollectionIndex,
        QdrantCollectionIndex,
    )

    from .indexes.tantivy.settings import (
        TantivyCollectionIndexSettings,
        TantivyCollectionIndexQuerySettings,
    )

    from .indexes.qdrant.settings import (
        QdrantCollectionIndexSettings,
        QdrantCollectionIndexQuerySettings,
    )


__all__ = (
    # hammad.data.collections.collection
    "Collection",
    "create_collection",
    "CollectionType",
    # hammad.data.collections.indexes
    "TantivyCollectionIndex",
    "QdrantCollectionIndex",
    "TantivyCollectionIndexSettings",
    "TantivyCollectionIndexQuerySettings",
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the ham.data.collections module."""
    return list(__all__)
