"""hammad.data"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .collections.base_collection import BaseCollection
    from .collections.searchable_collection import SearchableCollection
    from .collections.vector_collection import (
        VectorCollection,
    )
    from .collections.collection import (
        create_collection,
        VectorCollectionSettings,
        SearchableCollectionSettings,
    )
    from .databases.database import (
        Database,
        create_database,
    )
    from .types.files.file import File, FileSource
    from .types.files.audio import Audio
    from .types.files.image import Image
    from .types.files.configuration import Configuration
    from .types.files.document import Document


__all__ = (
    "create_collection",
    "VectorCollection",
    "VectorCollectionSettings",
    "SearchableCollection",
    "SearchableCollectionSettings",
    "BaseCollection",
    "create_database",
    "Database",
    "File",
    "FileSource",
    "Audio",
    "Image",
    "Configuration",
    "Document",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data module."""
    return list(__all__)
