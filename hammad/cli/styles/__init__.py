"""hammad.cli.styles

Contains resources, types and other utilities in context of
styling rendered content in the CLI. Most resources within this
submodule are not meant for direct use."""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .settings import (
        CLIStyleRenderableSettings,
        CLIStyleLiveSettings,
        CLIStyleBackgroundSettings,
    )
    from .types import (
        CLIStyleBackgroundType,
        CLIStyleBoxName,
        CLIStyleColorName,
        CLIStyleError,
        CLIStyleJustifyMethod,
        CLIStyleOverflowMethod,
        CLIStyleStyleName,
        CLIStyleType,
        CLIStyleVerticalOverflowMethod,
    )
    from .utils import live_render, style_renderable


__all__ = (
    # hammad.cli.styles.settings
    "CLIStyleRenderableSettings",
    "CLIStyleLiveSettings",
    "CLIStyleBackgroundSettings",
    # hammad.cli.styles.types
    "CLIStyleBackgroundType",
    "CLIStyleBoxName",
    "CLIStyleColorName",
    "CLIStyleError",
    "CLIStyleJustifyMethod",
    "CLIStyleOverflowMethod",
    "CLIStyleStyleName",
    "CLIStyleType",
    "CLIStyleVerticalOverflowMethod",
    # hammad.cli.styles.utils
    "live_render",
    "style_renderable",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
