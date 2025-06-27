"""hammad.data.databases"""

from typing import TYPE_CHECKING
from ...based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .database import Database, create_database


__all__ = (
    "Database",
    "create_database",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the data.databases module."""
    return list(__all__)
