"""hammad.cli.styles.settings"""

from typing import Any
from typing_extensions import TypedDict, NotRequired

from .types import (
    CLIStyleColorName,
    CLIStyleBoxName,
    CLIStyleJustifyMethod,
    CLIStyleOverflowMethod,
    CLIStyleVerticalOverflowMethod,
)

__all__ = (
    "CLIStyleRenderableSettings",
    "CLIStyleBackgroundSettings",
    "CLIStyleLiveSettings",
)


class CLIStyleRenderableSettings(TypedDict, total=False):
    """Extended dictionary definition of settings that can be
    applied to style various renderable content. These settings
    extend the settings within `rich.text.Text` and
    `rich.style.Style`.

    When using various stylable modules in the `hammad` package,
    you can either define the `style` parameter with a rich string
    tag with a color / style name. or apply the `style_settings`
    parameter with these settings."""

    color: NotRequired[CLIStyleColorName]
    """The color of the renderable output or content."""

    # rich.text

    justify: NotRequired[CLIStyleJustifyMethod]
    """The justification of the renderable output or content."""
    overflow: NotRequired[CLIStyleOverflowMethod | int]
    """The overflow method of the renderable output or content."""
    no_wrap: NotRequired[bool]
    """Whether the renderable output or content should be wrapped."""
    end: NotRequired[str]
    """The end character of the renderable output or content."""
    tab_size: NotRequired[int]
    """The tab size of the renderable output or content."""
    spans: NotRequired[list[Any]]
    """The spans of the renderable output or content."""

    # rich.style

    bold: NotRequired[bool]
    """Whether the renderable output or content should be bold."""
    dim: NotRequired[bool]
    """Whether the renderable output or content should be dimmed."""
    italic: NotRequired[bool]
    """Whether the renderable output or content should be italicized."""
    underline: NotRequired[bool]
    """Whether the renderable output or content should be underlined."""
    blink: NotRequired[bool]
    """Whether the renderable output or content should blink."""
    blink2: NotRequired[bool]
    """Whether the renderable output or content should blink twice."""
    reverse: NotRequired[bool]
    """Whether the renderable output or content should be reversed."""
    conceal: NotRequired[bool]
    """Whether the renderable output or content should be concealed."""
    strike: NotRequired[bool]
    """Whether the renderable output or content should be struck through."""
    underline2: NotRequired[bool]
    """Whether the renderable output or content should be underlined twice."""
    frame: NotRequired[bool]
    """Whether the renderable output or content should be framed."""
    encircle: NotRequired[bool]
    """Whether the renderable output or content should be encircled."""
    overline: NotRequired[bool]
    """Whether the renderable output or content should be overlined."""
    link: NotRequired[str]
    """The link to be applied to the renderable output or content."""


class CLIStyleBackgroundSettings(TypedDict, total=False):
    """Extended dictionary definition of settings that can be
    applied to style various background content. These settings
    extend the settings within `rich.box.Box` and `rich.panel.Panel`.

    When using various stylable modules in the `hammad` package,
    you can either define the `bg` parameter with a rich string
    tag with a color / style name. or apply the `bg_settings`
    parameter with these settings."""

    box: NotRequired[CLIStyleBoxName]
    """The box style to be applied to the background."""
    title: NotRequired[str]
    """The title of the background."""
    subtitle: NotRequired[str]
    """The subtitle of the background."""
    title_align: NotRequired[CLIStyleJustifyMethod]
    """The alignment of the title."""
    subtitle_align: NotRequired[CLIStyleJustifyMethod]
    """The alignment of the subtitle."""
    safe_box: NotRequired[bool]
    """Whether the box should be safe."""
    expand: NotRequired[bool]
    """Whether the box should be expanded."""
    style: NotRequired[CLIStyleRenderableSettings]
    """The style of the background."""
    border_style: NotRequired[CLIStyleRenderableSettings]
    """The style of the border."""
    width: NotRequired[int]
    """The width of the background."""
    height: NotRequired[int]
    """The height of the background."""
    padding: NotRequired[int]
    """The padding of the background."""
    highlight: NotRequired[bool]
    """Whether the background should be highlighted."""


class CLIStyleLiveSettings(TypedDict, total=False):
    """Dictionary definition of settings for content rendered
    with `rich.live.Live`."""

    screen: NotRequired[bool]
    """Whether the live renderable should be displayed in a screen."""
    duration: NotRequired[float]
    """The duration of the live renderable."""
    refresh_rate: NotRequired[int]
    """The refresh rate of the live renderable."""
    auto_refresh: NotRequired[bool]
    """Whether the live renderable should be automatically refreshed."""
    transient: NotRequired[bool]
    """Whether the live renderable should be transient."""
    redirect_stdout: NotRequired[bool]
    """Whether the live renderable should redirect stdout."""
    redirect_stderr: NotRequired[bool]
    """Whether the live renderable should redirect stderr."""
    vertical_overflow: NotRequired[CLIStyleVerticalOverflowMethod]
    """The vertical overflow method of the live renderable."""
