"""hammad.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .plugins import print, input, animate
    from .styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )


__all__ = (
    "print",
    "input",
    "animate",
    "CLIStyleRenderableSettings",
    "CLIStyleBackgroundSettings",
    "CLIStyleLiveSettings",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the plugins module."""
    return list(__all__)
