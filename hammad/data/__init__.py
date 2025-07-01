"""hammad.data"""

from typing import TYPE_CHECKING
from ..performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .configurations import (
        Configuration,
        read_configuration_from_file,
        read_configuration_from_url,
        read_configuration_from_os_vars,
        read_configuration_from_os_prefix,
        read_configuration_from_dotenv,
    )
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
    # hammad.data.configurations
    "Configuration",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_vars",
    "read_configuration_from_os_prefix",
    "read_configuration_from_dotenv",

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


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data module."""
    return list(__all__)
