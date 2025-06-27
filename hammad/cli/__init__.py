"""hammad.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .plugins import print, input, animate


__all__ = (
    "print",
    "input",
    "animate",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the plugins module."""
    return list(__all__)
