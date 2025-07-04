"""hammad.data.databases"""

from typing import TYPE_CHECKING
from ...performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .database import Database, create_database


__all__ = (
    "Database",
    "create_database",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.databases module."""
    return list(__all__)
