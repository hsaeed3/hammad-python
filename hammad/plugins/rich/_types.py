"""hammad.plugins.rich._types

Contains helper aliases in relation to the rich library."""

from typing import Literal, Dict, Tuple, TypeAlias, List, Union, Callable
from typing_extensions import TypedDict, NotRequired, Required

from rich.live import (
    VerticalOverflowMethod as RichVerticalOverflowMethod,
    Live as RichLive,
)
from rich.logging import RichHandler as RichRichHandler
from rich.progress import Progress as RichProgress
from rich.spinner import Spinner as RichSpinner
from rich.text import (
    Span as RichSpan,
)
from rich.align import AlignMethod as RichAlignMethod
from rich.panel import Panel as RichPanel
from rich.text import Text as RichText
from rich.style import Style as RichStyle
from rich.console import (
    Console as RichConsole,
    RenderableType as RichRenderableType,
)

__all__ = (
    "RichLive",
    "RichConsole",
    "RichProgress",
    "RichSpinner",
    "RichPanel",
    "RichText",
    "RichStyle",
    "RichBackgroundType",
    "RichRenderableType",
    "RichColorHex",
    "RichColorTuple",
    "RichColorName",
    "RichStyleSettings",
    "RichTextSettings",
    "RichBackgroundSettings",
    "RichRenderableSettings",
    "RichLiveSettings",
)


LoggingLevelName: TypeAlias = Literal[
    "debug",
    "info",
    "warning",
    "error",
    "critical",
]


RichJustifyMethod: TypeAlias = Literal[
    "left",
    "center",
    "right",
    "full",
    "default",
]
"""Literal helper alias providing type hinting for the various compatible
justify methods within the `rich` library."""


RichOverflowMethod: TypeAlias = Literal[
    "crop",
    "fold",
    "ellipsis",
    "ignore",
]
"""Literal helper alias providing type hinting for the various compatible
overflow methods within the `rich` library."""


RichColorHex: TypeAlias = str
"""Simple alias for the string type used to represent hex color values."""


RichColorTuple: TypeAlias = Tuple[int, int, int]
"""Simple alias for the tuple type used to represent RGB color values."""


RichColorName: TypeAlias = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
    "grey0",
    "navy_blue",
    "dark_blue",
    "blue3",
    "blue1",
    "dark_green",
    "deep_sky_blue4",
    "dodger_blue3",
    "dodger_blue2",
    "green4",
    "spring_green4",
    "turquoise4",
    "deep_sky_blue3",
    "dodger_blue1",
    "dark_cyan",
    "light_sea_green",
    "deep_sky_blue2",
    "deep_sky_blue1",
    "green3",
    "spring_green3",
    "cyan3",
    "dark_turquoise",
    "turquoise2",
    "green1",
    "spring_green2",
    "spring_green1",
    "medium_spring_green",
    "cyan2",
    "cyan1",
    "purple4",
    "purple3",
    "blue_violet",
    "grey37",
    "medium_purple4",
    "slate_blue3",
    "royal_blue1",
    "chartreuse4",
    "pale_turquoise4",
    "steel_blue",
    "steel_blue3",
    "cornflower_blue",
    "dark_sea_green4",
    "cadet_blue",
    "sky_blue3",
    "chartreuse3",
    "sea_green3",
    "aquamarine3",
    "medium_turquoise",
    "steel_blue1",
    "sea_green2",
    "sea_green1",
    "dark_slate_gray2",
    "dark_red",
    "dark_magenta",
    "orange4",
    "light_pink4",
    "plum4",
    "medium_purple3",
    "slate_blue1",
    "wheat4",
    "grey53",
    "light_slate_grey",
    "medium_purple",
    "light_slate_blue",
    "yellow4",
    "dark_sea_green",
    "light_sky_blue3",
    "sky_blue2",
    "chartreuse2",
    "pale_green3",
    "dark_slate_gray3",
    "sky_blue1",
    "chartreuse1",
    "light_green",
    "aquamarine1",
    "dark_slate_gray1",
    "deep_pink4",
    "medium_violet_red",
    "dark_violet",
    "purple",
    "medium_orchid3",
    "medium_orchid",
    "dark_goldenrod",
    "rosy_brown",
    "grey63",
    "medium_purple2",
    "medium_purple1",
    "dark_khaki",
    "navajo_white3",
    "grey69",
    "light_steel_blue3",
    "light_steel_blue",
    "dark_olive_green3",
    "dark_sea_green3",
    "light_cyan3",
    "light_sky_blue1",
    "green_yellow",
    "dark_olive_green2",
    "pale_green1",
    "dark_sea_green2",
    "pale_turquoise1",
    "red3",
    "deep_pink3",
    "magenta3",
    "dark_orange3",
    "indian_red",
    "hot_pink3",
    "hot_pink2",
    "orchid",
    "orange3",
    "light_salmon3",
    "light_pink3",
    "pink3",
    "plum3",
    "violet",
    "gold3",
    "light_goldenrod3",
    "tan",
    "misty_rose3",
    "thistle3",
    "plum2",
    "yellow3",
    "khaki3",
    "light_yellow3",
    "grey84",
    "light_steel_blue1",
    "yellow2",
    "dark_olive_green1",
    "dark_sea_green1",
    "honeydew2",
    "light_cyan1",
    "red1",
    "deep_pink2",
    "deep_pink1",
    "magenta2",
    "magenta1",
    "orange_red1",
    "indian_red1",
    "hot_pink",
    "medium_orchid1",
    "dark_orange",
    "salmon1",
    "light_coral",
    "pale_violet_red1",
    "orchid2",
    "orchid1",
    "orange1",
    "sandy_brown",
    "light_salmon1",
    "light_pink1",
    "pink1",
    "plum1",
    "gold1",
    "light_goldenrod2",
    "navajo_white1",
    "misty_rose1",
    "thistle1",
    "yellow1",
    "light_goldenrod1",
    "khaki1",
    "wheat1",
    "cornsilk1",
    "grey100",
    "grey3",
    "grey7",
    "grey11",
    "grey15",
    "grey19",
    "grey23",
    "grey27",
    "grey30",
    "grey35",
    "grey39",
    "grey42",
    "grey46",
    "grey50",
    "grey54",
    "grey58",
    "grey62",
    "grey66",
    "grey70",
    "grey74",
    "grey78",
    "grey82",
    "grey85",
    "grey89",
    "grey93",
    "default",
]
"""Literal helper alias providing type hinting for the various compatible color names
within the `rich` library."""


RichColorType: TypeAlias = RichColorName | RichColorHex | RichColorTuple
"""Union type accepting either a color name, hex value, or RGB tuple."""


RichStyleName: TypeAlias = Literal[
    "dim",
    "d",
    "bold",
    "b",
    "italic",
    "i",
    "underline",
    "u",
    "blink",
    "blink2",
    "reverse",
    "r",
    "conceal",
    "c",
    "strike",
    "s",
    "underline2",
    "uu",
    "frame",
    "encircle",
    "overline",
    "o",
    "on",
    "not",
    "link",
    "none",
]
"""Literal helper alias providing type hinting for the various compatible
style names within the `rich` library."""


RichBoxName: TypeAlias = Literal[
    "ascii",
    "ascii2",
    "ascii_double_head",
    "square",
    "square_double_head",
    "minimal",
    "minimal_heavy_head",
    "minimal_double_head",
    "simple",
    "simple_head",
    "simple_heavy",
    "horizontals",
    "rounded",
    "heavy",
    "heavy_edge",
    "heavy_head",
    "double",
    "double_edge",
    "markdown",
]


class RichStyleSettings(TypedDict, total=False):
    """Helper dictionary type used to define the 'style' of a renderable output
    or content through the `rich` library."""

    # extended rich color type

    color: NotRequired[RichColorName | RichColorHex | RichColorTuple]
    """The color of the renderable output or content."""

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


class RichTextSettings(TypedDict, total=False):
    """Helper dictionary type used to define the 'text' of a renderable output
    or content through the `rich` library."""

    justify: NotRequired[RichJustifyMethod]
    """The justification of the renderable output or content."""

    overflow: NotRequired[RichOverflowMethod | int]
    """The overflow method of the renderable output or content."""

    no_wrap: NotRequired[bool]
    """Whether the renderable output or content should be wrapped."""

    end: NotRequired[str]
    """The end character of the renderable output or content."""

    tab_size: NotRequired[int]
    """The tab size of the renderable output or content."""

    spans: NotRequired[List[RichSpan]]
    """The spans of the renderable output or content."""


class RichBackgroundSettings(TypedDict, total=False):
    """Helper configuration dictionary used to define the 'background'
    of various renderable components. This extends settings found within
    rich.box, rich.panel."""

    color: NotRequired[RichColorName | RichColorHex | RichColorTuple]
    """The color of the background."""

    box: NotRequired[RichBoxName]
    """Defines the name of the box style to be used for the background"""

    title: NotRequired[str]
    """The title of the background."""

    subtitle: NotRequired[str]
    """The subtitle of the background."""

    title_align: NotRequired[RichAlignMethod]
    """The alignment of the title."""

    subtitle_align: NotRequired[RichAlignMethod]
    """The alignment of the subtitle."""

    safe_box: NotRequired[bool]
    """Whether the box should be safe."""

    expand: NotRequired[bool]
    """Whether the box should be expanded."""

    style: NotRequired[RichStyleSettings]
    """The style of the background."""

    border_style: NotRequired[RichStyleSettings]
    """The style of the border."""

    width: NotRequired[int]
    """The width of the background."""

    height: NotRequired[int]
    """The height of the background."""

    padding: NotRequired[int]
    """The padding of the background."""

    highlight: NotRequired[bool]
    """Whether the background should be highlighted."""


RichBackgroundType: TypeAlias = RichColorType | RichBackgroundSettings
"""Union type used for the `background` parameter of various components within the
framework."""


class RichRenderableSettings(RichTextSettings, RichTextSettings):
    """Helper configuration dictionary used to define the 'renderable'
    of various renderable components. This extends settings found within
    rich.box, rich.panel."""

    background: NotRequired[RichBackgroundType]
    """The background of the renderable output or content."""


RichStyleType: TypeAlias = RichColorType | RichStyleName | RichRenderableSettings
"""Union type used for the `style` parameter of various components within the
framework."""


class RichLiveSettings(TypedDict, total=False):
    """Helper configuration dictionary used to define the 'live'
    of various renderable components. This extends settings found within
    rich.live."""

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

    vertical_overflow: NotRequired[RichVerticalOverflowMethod]
    """The vertical overflow method of the live renderable."""


class RichLoggingLevelSettings(TypedDict, total=False):
    """Helper style configuration for a single logging level."""

    show_name: NotRequired[bool]
    """Whether to show the logging level's name."""

    show_level: NotRequired[bool]
    """Whether to show the logging level."""

    show_time: NotRequired[bool]
    """Whether to show the logging time."""

    background: NotRequired[RichBackgroundType]
    """The background of the logging level."""

    style: NotRequired[RichStyleType]
    """Combined style for both the background and the message.
    
    If either level_style or message_style is provided, this
    will be ignored for that portion."""

    level_style: NotRequired[RichStyleType]
    """The style of the logging level's name."""

    message_style: NotRequired[RichStyleType]
    """The style of the logging level's message."""


RichDefaultLoggingLevelSettings: Dict[LoggingLevelName, RichLoggingLevelSettings] = {
    "debug": {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "level_style": "white",
        "message_style": "dim italic white",
    },
    "info": {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "style": "white",
    },
    "warning": {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "level_style": "bold yellow",
        "message_style": "italic yellow",
    },
    "error": {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "level_style": "bold red",
        "message_style": "italic red",
    },
    "critical": {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "style": "bold red",
    },
}
"""Default logging level settings for the `hammad.logging.Logger` module."""


class RichLoggingSettings(TypedDict, total=False):
    """Helper configuration dictionary used to define the 'logging'
    of various renderable components. This extends settings found within
    rich.logging.

    Any specific overrides added to 'levels' or new levels created,
    will override these global defaults.

    When using the `hammad.logging.Logger` module, if any
    style / background settings are given, the logger will utilize
    a rich handler."""

    name: NotRequired[str]
    """The name of the logging instance."""

    prefix: NotRequired[str]
    """A prefix to add before the logger's name."""

    levels: NotRequired[Dict[LoggingLevelName | str, RichLoggingLevelSettings]]
    """A dictionary containing either override styles for existing
    logging levels, or new levels to be created."""

    style: NotRequired[RichStyleType]
    """The style of the logging instance. This only applies to it's name"""

    background: NotRequired[RichBackgroundType]
    """The background of the logging instance."""

    show_name: NotRequired[bool]
    """Whether to show the logging instance's name."""

    show_level: NotRequired[bool]
    """Whether to show the logging instance's level."""

    show_time: NotRequired[bool]
    """Whether to show the logging instance's time."""

    show_path: NotRequired[bool]
    """Whether to show the logging instance's path."""

    show_module: NotRequired[bool]
    """Whether to show the logging instance's module."""

    show_function: NotRequired[bool]
    """Whether to show the logging instance's function."""
