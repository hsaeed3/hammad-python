"""hammad.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .plugins import print, input, animate
    from ._runner import CLIRunner
    from .styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )


__all__ = (
    "print",
    "input",
    "animate",
    "CLIRunner",
    "CLIStyleRenderableSettings",
    "CLIStyleBackgroundSettings",
    "CLIStyleLiveSettings",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the plugins module."""
    return list(__all__)
