"""ham.core.cli

Contains resources for styling rendered CLI content as well
as extensions / utilities for creating CLI interfaces."""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer

if TYPE_CHECKING:
    from .logs import log, log_iterable, log_progress
    from .plugins import print, input, animate
    from .styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )


__all__ = (
    # ham.core.cli.plugins
    "print",
    "input",
    "animate",
    # ham.core.cli.logs
    "log",
    "log_iterable",
    "log_progress",
    # ham.core.cli.styles.settings
    "CLIStyleRenderableSettings",
    "CLIStyleBackgroundSettings",
    "CLIStyleLiveSettings",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the plugins module."""
    return list(__all__)
