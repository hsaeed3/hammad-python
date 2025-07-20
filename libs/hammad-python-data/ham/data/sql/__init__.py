"""hammad.data.sql"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .types import DatabaseItemType, DatabaseItem
    from .database import Database, create_database


__all__ = (
    "DatabaseItemType",
    "DatabaseItem",
    "Database",
    "create_database",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data.sql module."""
    return list(__all__)
