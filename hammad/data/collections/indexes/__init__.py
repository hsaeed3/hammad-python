"""hammad.data.collections.indexes"""

from typing import TYPE_CHECKING
from ...._internal import create_getattr_importer

if TYPE_CHECKING:
    from .tantivy.index import TantivyCollectionIndex
    from .qdrant.index import QdrantCollectionIndex

    from .tantivy.settings import (
        TantivyCollectionIndexSettings,
        TantivyCollectionIndexQuerySettings,
    )
    from .qdrant.settings import (
        QdrantCollectionIndexSettings,
        QdrantCollectionIndexQuerySettings,
        DistanceMetric,
    )


__all__ = (
    "TantivyCollectionIndex",
    "QdrantCollectionIndex",
    "TantivyCollectionIndexSettings",
    "TantivyCollectionIndexQuerySettings",
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
    "DistanceMetric",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data.collections.indexes module."""
    return list(__all__)
