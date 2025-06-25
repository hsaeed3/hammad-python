"""hammad._internal._style_types

Contains internal types used extensively throughout the package
for styling rendered content with the `rich` library."""

from typing import Literal, TypedDict, NotRequired, Any
from typing_extensions import TypeAliasType

__all__ = (
    "StyleError",
    "StyleVerticalOverflowMethod",
    "StyleJustifyMethod",
    "StyleOverflowMethod",
    "StyleColorName",
    "StyleStyleName",
    "StyleBoxName",
    "StyleLiveSettings",
    "StyleStyleSettings",
    "StyleBackgroundSettings",
)


class StyleError(Exception):
    """Exception raised for any errors related to rich styling
    of rendered content."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


StyleVerticalOverflowMethod = TypeAliasType(
    "StyleVerticalOverflowMethod",
    Literal[
        "crop",
        "ellipsis",
        "visible",
    ],
)
"""Literal helper alias providing type hinting for the various compatible
vertical overflow methods within the `rich` library."""


StyleJustifyMethod = TypeAliasType(
    "StyleJustifyMethod",
    Literal[
        "left",
        "center",
        "right",
    ],
)
"""Literal helper alias providing type hinting for the various compatible
justify methods within the `rich` library."""


StyleOverflowMethod = TypeAliasType(
    "StyleOverflowMethod",
    Literal[
        "crop",
        "fold",
        "ellipsis",
        "ignore",
    ],
)
"""Literal helper alias providing type hinting for the various compatible
overflow methods within the `rich` library."""


StyleColorName = TypeAliasType(
    "StyleColorName",
    Literal[
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
    ],
)
"""Literal helper alias providing type hinting for the various compatible color names
within the `rich` library."""


StyleStyleName = TypeAliasType(
    "StyleStyleName",
    Literal[
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
    ],
)
"""Literal helper alias providing type hinting for the various compatible
style names within the `rich` library."""


StyleBoxName = TypeAliasType(
    "StyleBoxName",
    Literal[
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
    ],
)
"""Literal helper alias providing type hinting for the various compatible
box names within the `rich` library."""


class StyleLiveSettings(TypedDict, total=False):
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

    vertical_overflow: NotRequired[StyleVerticalOverflowMethod]
    """The vertical overflow method of the live renderable."""


class StyleStyleSettings(TypedDict, total=False):
    """Helper configuration dictionary used to define the `style`
    of various Print components and methods. This defines the style of
    the rendered text content itself, not it's background or other
    visual elements."""

    color: NotRequired[str | StyleColorName]
    """The color to render the text content in."""

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

    # rich.text

    justify: NotRequired[StyleJustifyMethod]
    """The justification of the renderable output or content."""

    overflow: NotRequired[StyleOverflowMethod | int]
    """The overflow method of the renderable output or content."""

    no_wrap: NotRequired[bool]
    """Whether the renderable output or content should be wrapped."""

    end: NotRequired[str]
    """The end character of the renderable output or content."""

    tab_size: NotRequired[int]
    """The tab size of the renderable output or content."""

    spans: NotRequired[list[Any]]
    """The spans of the renderable output or content."""


class StyleBackgroundSettings(TypedDict, total=False):
    """Helper configuration dictionary used to define the `background`
    of various Print components and methods. This defines the background
    of the rendered text content itself, not it's style or other
    visual elements."""

    color: NotRequired[str | StyleColorName]
    """The color of the background."""

    box: NotRequired[StyleBoxName]
    """Defines the name of the box style to be used for the background"""

    title: NotRequired[str]
    """The title of the background."""

    subtitle: NotRequired[str]
    """The subtitle of the background."""

    title_align: NotRequired[StyleJustifyMethod]
    """The alignment of the title."""

    subtitle_align: NotRequired[StyleJustifyMethod]
    """The alignment of the subtitle."""

    safe_box: NotRequired[bool]
    """Whether the box should be safe."""

    expand: NotRequired[bool]
    """Whether the box should be expanded."""

    style: NotRequired[StyleStyleSettings]
    """The style of the background."""

    border_style: NotRequired[StyleStyleSettings]
    """The style of the border."""

    width: NotRequired[int]
    """The width of the background."""

    height: NotRequired[int]
    """The height of the background."""

    padding: NotRequired[int]
    """The padding of the background."""

    highlight: NotRequired[bool]
    """Whether the background should be highlighted."""
