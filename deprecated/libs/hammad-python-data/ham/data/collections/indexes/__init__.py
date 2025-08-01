"""ham.data.collections.indexes"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from .....core._internal import type_checking_importer  # type: ignore

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


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data.collections.indexes module."""
    return list(__all__)
