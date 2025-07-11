"""hammad.data.collections"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .collection import (
        Collection,
        create_collection,
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
    # hammad.data.collections.indexes
    "TantivyCollectionIndex",
    "QdrantCollectionIndex",
    "TantivyCollectionIndexSettings",
    "TantivyCollectionIndexQuerySettings",
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data.collections module."""
    return list(__all__)
