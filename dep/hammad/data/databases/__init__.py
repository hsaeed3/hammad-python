"""hammad.data.databases"""

from typing import TYPE_CHECKING
from ..._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .database import Database, create_database


__all__ = (
    "Database",
    "create_database",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.databases module."""
    return list(__all__)
