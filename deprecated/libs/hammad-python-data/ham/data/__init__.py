"""ham.data

```markdown
## `hammad-python-data`
```
"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ..core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from .collections import (
        Collection,
        create_collection,
        CollectionType,
        TantivyCollectionIndex,
        QdrantCollectionIndex,
        TantivyCollectionIndexSettings,
        TantivyCollectionIndexQuerySettings,
        QdrantCollectionIndexSettings,
        QdrantCollectionIndexQuerySettings,
    )
    from .sql import DatabaseItemType, DatabaseItem, Database, create_database


__all__ = (
    # hammad.data.collections
    "Collection",
    "create_collection",
    "CollectionType",
    "TantivyCollectionIndex",
    "QdrantCollectionIndex",
    "TantivyCollectionIndexSettings",
    "TantivyCollectionIndexQuerySettings",
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
    # hammad.data.sql
    "DatabaseItemType",
    "DatabaseItem",
    "Database",
    "create_database",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the ham.data module."""
    return list(__all__)
