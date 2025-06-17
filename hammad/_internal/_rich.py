"""hammad.cli._rich

This provides a number of type aliases and helper classes used within
the `hammad` package to integrate with the `rich` library. This module
is used as the internal resource for all `rich` components."""

from typing import Literal, Dict, Tuple, TypeAlias, List
from typing_extensions import TypedDict, NotRequired, Required

from rich import get_console as get_rich_console
from rich.color import Color as RichColor
from rich.console import (
    Console as RichConsole,
    ConsoleOptions as RichConsoleOptions,
    RenderableType as RichRenderableType,
    RenderResult as RichRenderResult,
    Segment as RichSegment,
)
from rich.live import Live as RichLive
from rich.panel import Panel as RichPanel, AlignMethod as RichAlignMethod
from rich.style import Style as RichStyle
from rich.text import (
    Text as RichText,
    Span as RichSpan,
)
from rich.box import Box as RichBox

__all__ = (
    "get_rich_console",
    "RichColor",
    "RichConsole",
    "RichConsoleOptions",
    "RichRenderableType",
    "RichRenderResult",
    "RichSegment",
    "RichLive",
    "RichPanel",
    "RichAlignMethod",
    "RichStyle",
    "RichText",
    "RichSpan",
    "RichBox",
    "RichJustifyMethod",
    "RichOverflowMethod",
    "RichColorTuple",
    "RichColorHex",
    "RichColorName",
    "RichColorType",
    "RichBoxName",
    "RichStyleSettings",
    "RichBackgroundSettings",
    "wrap_renderable_with_rich_config",
)


RichJustifyMethod: TypeAlias = Literal["default", "left", "center", "right", "full"]


RichOverflowMethod: TypeAlias = Literal["fold", "crop", "ellipsis", "ignore"]


RichColorTuple: TypeAlias = Tuple[int, int, int]
"""Simple alias for the tuple type used to represent RGB color values."""


RichColorHex: TypeAlias = str
"""Simple alias for the string type used to represent hex color values."""


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
]
"""Literal helper alias providing type hinting for the various compatible color names
within the `rich` library."""


RichColorType: TypeAlias = RichColorName | RichColorHex | RichColorTuple


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

    # NOTE : rich.text Specific

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


def wrap_renderable_with_rich_config(
    r: RichRenderableType,
    style: RichColorType | RichStyleSettings,
    bg: RichColorType | RichBackgroundSettings,
    console: RichConsole = get_rich_console(),
) -> RichRenderableType:
    """Wraps a renderable with rich configuration.

    Args:
        r : The renderable to wrap.
        style : The style to apply to the renderable. (either a string
        color or a dictionary of style settings)
        background : The background to apply to the renderable. (either a
        string color or a dictionary of background settings)
        console : The console to use for rendering. (default: the global
        console)

    Returns:
        The wrapped renderable."""

    # Process style parameter
    if isinstance(style, dict):
        # Extract style properties from RichStyleSettings
        style_kwargs = {}

        # Handle color separately
        if "color" in style:
            color_value = style["color"]
            if isinstance(color_value, tuple):
                style_kwargs["color"] = (
                    f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                )
            else:
                style_kwargs["color"] = color_value

        # Handle all other style properties
        style_props = [
            "bold",
            "dim",
            "italic",
            "underline",
            "blink",
            "blink2",
            "reverse",
            "conceal",
            "strike",
            "underline2",
            "frame",
            "encircle",
            "overline",
            "link",
        ]

        for prop in style_props:
            if prop in style:
                style_kwargs[prop] = style[prop]

        rich_style = RichStyle(**style_kwargs)
    else:
        # Simple color style
        if isinstance(style, tuple):
            rich_style = RichStyle(color=f"rgb({style[0]},{style[1]},{style[2]})")
        else:
            rich_style = RichStyle(color=style)

    # Apply style to renderable
    if isinstance(r, str):
        styled_renderable = RichText(r, style=rich_style)
    elif isinstance(r, RichText):
        # For existing Text objects, create a new one with the style
        styled_renderable = RichText(r.plain, style=rich_style)
    else:
        # For other renderables, we'll apply style through the Panel
        styled_renderable = r

    # Process background parameter
    if isinstance(bg, dict):
        # Extract panel properties from RichBackgroundSettings
        panel_kwargs = {}

        # Handle box style
        if "box" in bg:
            box_name = bg["box"]
            # Import box styles
            from rich import box as rich_box_module

            box_map = {
                "ascii": rich_box_module.ASCII,
                "ascii2": rich_box_module.ASCII2,
                "ascii_double_head": rich_box_module.ASCII_DOUBLE_HEAD,
                "square": rich_box_module.SQUARE,
                "square_double_head": rich_box_module.SQUARE_DOUBLE_HEAD,
                "minimal": rich_box_module.MINIMAL,
                "minimal_heavy_head": rich_box_module.MINIMAL_HEAVY_HEAD,
                "minimal_double_head": rich_box_module.MINIMAL_DOUBLE_HEAD,
                "simple": rich_box_module.SIMPLE,
                "simple_head": rich_box_module.SIMPLE_HEAD,
                "simple_heavy": rich_box_module.SIMPLE_HEAVY,
                "horizontals": rich_box_module.HORIZONTALS,
                "rounded": rich_box_module.ROUNDED,
                "heavy": rich_box_module.HEAVY,
                "heavy_edge": rich_box_module.HEAVY_EDGE,
                "heavy_head": rich_box_module.HEAVY_HEAD,
                "double": rich_box_module.DOUBLE,
                "double_edge": rich_box_module.DOUBLE_EDGE,
                "markdown": getattr(
                    rich_box_module, "MARKDOWN", rich_box_module.ROUNDED
                ),
            }
            panel_kwargs["box"] = box_map.get(box_name, rich_box_module.ROUNDED)

        # Handle panel-specific properties
        panel_props = [
            "title",
            "subtitle",
            "title_align",
            "subtitle_align",
            "safe_box",
            "expand",
            "width",
            "height",
            "padding",
            "highlight",
        ]

        for prop in panel_props:
            if prop in bg:
                panel_kwargs[prop] = bg[prop]

        # Handle style and border_style
        if "style" in bg:
            bg_style = bg["style"]
            if isinstance(bg_style, dict):
                # Process nested style settings
                bg_style_kwargs = {}
                if "color" in bg_style:
                    color_value = bg_style["color"]
                    if isinstance(color_value, tuple):
                        bg_style_kwargs["bgcolor"] = (
                            f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                        )
                    else:
                        bg_style_kwargs["bgcolor"] = color_value
                panel_kwargs["style"] = RichStyle(**bg_style_kwargs)
            else:
                # Simple color background
                if isinstance(bg_style, tuple):
                    panel_kwargs["style"] = RichStyle(
                        bgcolor=f"rgb({bg_style[0]},{bg_style[1]},{bg_style[2]})"
                    )
                else:
                    panel_kwargs["style"] = RichStyle(bgcolor=bg_style)

        if "border_style" in bg:
            border_style = bg["border_style"]
            if isinstance(border_style, dict):
                # Process border style settings
                border_style_kwargs = {}
                if "color" in border_style:
                    color_value = border_style["color"]
                    if isinstance(color_value, tuple):
                        border_style_kwargs["color"] = (
                            f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                        )
                    else:
                        border_style_kwargs["color"] = color_value

                # Add other border style properties
                for prop in ["bold", "dim", "italic"]:
                    if prop in border_style:
                        border_style_kwargs[prop] = border_style[prop]

                panel_kwargs["border_style"] = RichStyle(**border_style_kwargs)

        # Handle background color if specified at top level
        if "color" in bg and "style" not in bg:
            color_value = bg["color"]
            if isinstance(color_value, tuple):
                panel_kwargs["style"] = RichStyle(
                    bgcolor=f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                )
            else:
                panel_kwargs["style"] = RichStyle(bgcolor=color_value)

        # For non-text renderables that weren't styled, apply the style through panel
        if not isinstance(r, (str, RichText)) and not isinstance(
            styled_renderable, (RichText)
        ):
            # Apply the style to the panel instead
            if "style" in panel_kwargs:
                # Merge foreground style into panel style
                existing_style = panel_kwargs["style"]
                merged_style_dict = {}

                # Get existing bgcolor if any
                if hasattr(existing_style, "_bgcolor") and existing_style._bgcolor:
                    merged_style_dict["bgcolor"] = str(existing_style._bgcolor)

                # Add foreground style attributes
                if hasattr(rich_style, "_color") and rich_style._color:
                    merged_style_dict["color"] = str(rich_style._color)
                for attr in [
                    "_bold",
                    "_dim",
                    "_italic",
                    "_underline",
                    "_blink",
                    "_blink2",
                    "_reverse",
                    "_conceal",
                    "_strike",
                    "_underline2",
                    "_frame",
                    "_encircle",
                    "_overline",
                ]:
                    if hasattr(rich_style, attr) and getattr(rich_style, attr):
                        merged_style_dict[attr[1:]] = True

                panel_kwargs["style"] = RichStyle(**merged_style_dict)
            else:
                # No existing panel style, so we can use the rich_style with bgcolor
                panel_kwargs["style"] = rich_style

        # Create panel with all settings
        final_renderable = RichPanel(styled_renderable, **panel_kwargs)
    else:
        # Simple background color
        if isinstance(bg, tuple):
            bg_style = RichStyle(bgcolor=f"rgb({bg[0]},{bg[1]},{bg[2]})")
        else:
            bg_style = RichStyle(bgcolor=bg)

        # For non-text renderables with simple bg, merge styles
        if not isinstance(r, (str, RichText)) and not isinstance(
            styled_renderable, (RichText)
        ):
            # Merge foreground and background styles
            merged_style_dict = {"bgcolor": bg_style._bgcolor}

            if hasattr(rich_style, "_color") and rich_style._color:
                merged_style_dict["color"] = str(rich_style._color)
            for attr in [
                "_bold",
                "_dim",
                "_italic",
                "_underline",
                "_blink",
                "_blink2",
                "_reverse",
                "_conceal",
                "_strike",
                "_underline2",
                "_frame",
                "_encircle",
                "_overline",
            ]:
                if hasattr(rich_style, attr) and getattr(rich_style, attr):
                    merged_style_dict[attr[1:]] = True

            final_renderable = RichPanel(
                styled_renderable, style=RichStyle(**merged_style_dict)
            )
        else:
            final_renderable = RichPanel(styled_renderable, style=bg_style)

    return final_renderable
