"""hammad.data.sql"""

from typing import TYPE_CHECKING
try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ..._internal import type_checking_importer # type: ignore


if TYPE_CHECKING:
    from .types import DatabaseItemType, DatabaseItem
    from .database import Database, create_database


__all__ = (
    "DatabaseItemType",
    "DatabaseItem",
    "Database",
    "create_database",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data.sql module."""
    return list(__all__)
