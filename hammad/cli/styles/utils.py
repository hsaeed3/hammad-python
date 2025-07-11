"""hammad.cli.styles.utils"""

import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich import get_console as get_rich_console
    from rich.console import Console, RenderableType
    from rich.live import Live
    from rich.panel import Panel
    from rich.style import Style
    from rich.text import Text

from .types import (
    CLIStyleError,
    CLIStyleType,
    CLIStyleBackgroundType,
)
from .settings import (
    CLIStyleRenderableSettings,
    CLIStyleBackgroundSettings,
    CLIStyleLiveSettings,
)

# Lazy import cache for rich components
_RICH_CACHE = {}


def _get_rich_console():
    """Lazy import for rich console"""
    if "get_console" not in _RICH_CACHE:
        from rich import get_console as get_rich_console

        _RICH_CACHE["get_console"] = get_rich_console
    return _RICH_CACHE["get_console"]


def _get_rich_classes():
    """Lazy import for rich classes"""
    if "classes" not in _RICH_CACHE:
        from rich.console import Console, RenderableType
        from rich.live import Live
        from rich.panel import Panel
        from rich.style import Style
        from rich.text import Text

        _RICH_CACHE["classes"] = {
            "Console": Console,
            "RenderableType": RenderableType,
            "Live": Live,
            "Panel": Panel,
            "Style": Style,
            "Text": Text,
        }
    return _RICH_CACHE["classes"]


def live_render(
    r,
    live_settings: CLIStyleLiveSettings,
    console=None,
) -> None:
    """Runs a rich live renderable.

    Args:
        r : The renderable to run.
        settings : The settings to use for the live renderable.
        console : The console to use for the live renderable."""

    rich_classes = _get_rich_classes()
    RenderableType = rich_classes["RenderableType"]
    Live = rich_classes["Live"]

    if console is None:
        get_rich_console = _get_rich_console()
        console = get_rich_console()

    if not isinstance(r, RenderableType):
        raise CLIStyleError("The renderable must be a RenderableType.")

    if not live_settings.get("duration"):
        duration = 2.0
    else:
        duration = live_settings["duration"]
    if "duration" in live_settings:
        del live_settings["duration"]

    if not live_settings.get("refresh_rate"):
        refresh_rate = 20
    else:
        refresh_rate = live_settings["refresh_rate"]
    if "refresh_rate" in live_settings:
        del live_settings["refresh_rate"]

    if not live_settings.get("auto_refresh"):
        live_settings["auto_refresh"] = True
    if not live_settings.get("transient"):
        live_settings["transient"] = False
    if not live_settings.get("redirect_stdout"):
        live_settings["redirect_stdout"] = True
    if not live_settings.get("redirect_stderr"):
        live_settings["redirect_stderr"] = True
    if not live_settings.get("vertical_overflow"):
        live_settings["vertical_overflow"] = "ellipsis"

    try:
        with Live(r, console=console, **live_settings) as live:
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1 / refresh_rate)
                live.refresh()
    except Exception as e:
        raise CLIStyleError(f"Error running rich live: {e}") from e


def style_renderable(
    r,
    style: CLIStyleType | None = None,
    style_settings: CLIStyleRenderableSettings | None = None,
    bg: CLIStyleBackgroundType | None = None,
    bg_settings: CLIStyleBackgroundSettings | None = None,
    border=None,
    padding=None,
    title: str | None = None,
    expand: bool | None = None,
):
    """Styles a renderable with a rich string tag or settings.

    Args:
        r : The renderable to style.
        style : The rich string tag to apply to the renderable.
        style_settings : The settings to apply to the renderable.
        bg : The rich string tag to apply to the background.
        bg_settings : The settings to apply to the background.
        border : Border style for panel rendering.
        padding : Padding dimensions for panel rendering.
        title : Title for panel rendering.
        expand : Whether to expand panel to full width.
    """

    try:
        rich_classes = _get_rich_classes()
        Style = rich_classes["Style"]
        Text = rich_classes["Text"]
        Panel = rich_classes["Panel"]

        # First handle style processing to get styled_renderable
        styled_renderable = r

        # Handle string-based styles (including color tags and complex styles)
        if isinstance(style, str):
            try:
                # For strings, use Rich's style parsing directly to support things like 'black on red'
                rich_style = Style.parse(style)
                styled_renderable = (
                    Text(r, style=rich_style) if isinstance(r, str) else r
                )
            except Exception:
                # Fallback to treating as simple color if parsing fails
                rich_style = Style(color=style)
                styled_renderable = (
                    Text(r, style=rich_style) if isinstance(r, str) else r
                )

        # Handle tuple-based styles (RGB color tuples)
        elif isinstance(style, tuple):
            try:
                # Convert tuple to RGB format for Rich
                rgb_color = f"rgb({style[0]},{style[1]},{style[2]})"
                rich_style = Style(color=rgb_color)
                styled_renderable = (
                    Text(r, style=rich_style) if isinstance(r, str) else r
                )
            except Exception:
                # Fallback to original renderable if tuple processing fails
                styled_renderable = r

        # Handle dict-based styles passed as style parameter
        elif isinstance(style, dict):
            try:
                # Process text/style properties from dict
                text_style_kwargs = {}

                # Handle color from style dict
                if "color" in style:
                    try:
                        color_value = style["color"]
                        if isinstance(color_value, tuple):
                            text_style_kwargs["color"] = (
                                f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                            )
                        else:
                            text_style_kwargs["color"] = color_value
                    except Exception:
                        # Skip color if processing fails
                        pass

                # Handle text style properties
                text_style_props = [
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

                for prop in text_style_props:
                    if prop in style:
                        try:
                            text_style_kwargs[prop] = style[prop]
                        except Exception:
                            # Skip property if processing fails
                            continue

                # Create rich style from text properties
                try:
                    rich_style = (
                        Style(**text_style_kwargs) if text_style_kwargs else None
                    )
                except Exception:
                    rich_style = None

                # Apply text style to renderable
                try:
                    if isinstance(r, str):
                        styled_renderable = (
                            Text(r, style=rich_style) if rich_style else Text(r)
                        )
                    elif isinstance(r, Text) and rich_style:
                        styled_renderable = Text(r.plain, style=rich_style)
                    else:
                        styled_renderable = r
                except Exception:
                    styled_renderable = r

            except Exception:
                # Fallback to original renderable if dict processing fails
                styled_renderable = r

        # Handle style_settings dict
        elif style_settings:
            try:
                # Process text/style properties
                text_style_kwargs = {}

                # Handle color from style settings
                if "color" in style_settings:
                    try:
                        color_value = style_settings["color"]
                        if isinstance(color_value, tuple):
                            text_style_kwargs["color"] = (
                                f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                            )
                        else:
                            text_style_kwargs["color"] = color_value
                    except Exception:
                        # Skip color if processing fails
                        pass

                # Handle text style properties
                text_style_props = [
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

                for prop in text_style_props:
                    if prop in style_settings:
                        try:
                            text_style_kwargs[prop] = style_settings[prop]
                        except Exception:
                            # Skip property if processing fails
                            continue

                # Create rich style from text properties
                try:
                    rich_style = (
                        Style(**text_style_kwargs) if text_style_kwargs else None
                    )
                except Exception:
                    rich_style = None

                # Apply text style to renderable
                try:
                    if isinstance(r, str):
                        styled_renderable = (
                            Text(r, style=rich_style) if rich_style else Text(r)
                        )
                    elif isinstance(r, Text) and rich_style:
                        styled_renderable = Text(r.plain, style=rich_style)
                    else:
                        styled_renderable = r
                except Exception:
                    styled_renderable = r

            except Exception:
                # Fallback to original renderable if dict processing fails
                styled_renderable = r

        # Handle background settings (from bg or bg_settings parameter) or panel parameters
        if bg or bg_settings or border or padding or title or expand:
            try:
                if bg_settings:
                    # Full background configuration
                    panel_kwargs = {}

                    # Handle box style
                    if "box" in bg_settings:
                        try:
                            box_name = bg_settings["box"]
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
                                    rich_box_module,
                                    "MARKDOWN",
                                    rich_box_module.ROUNDED,
                                ),
                            }
                            panel_kwargs["box"] = box_map.get(
                                box_name, rich_box_module.ROUNDED
                            )
                        except Exception:
                            # Use default box if box processing fails
                            pass

                    # Handle panel properties
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
                        if prop in bg_settings:
                            try:
                                panel_kwargs[prop] = bg_settings[prop]
                            except Exception:
                                # Skip property if processing fails
                                continue

                    # Handle direct panel parameters
                    if title is not None:
                        panel_kwargs["title"] = title
                    if padding is not None:
                        panel_kwargs["padding"] = padding
                    if expand is not None:
                        panel_kwargs["expand"] = expand
                    if border is not None:
                        try:
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
                                    rich_box_module,
                                    "MARKDOWN",
                                    rich_box_module.ROUNDED,
                                ),
                            }
                            panel_kwargs["box"] = box_map.get(
                                border, rich_box_module.ROUNDED
                            )
                        except Exception:
                            # Use default box if box processing fails
                            pass

                    # Handle background style
                    if "style" in bg_settings:
                        try:
                            bg_style = bg_settings["style"]
                            if isinstance(bg_style, dict):
                                bg_style_kwargs = {}
                                if "color" in bg_style:
                                    try:
                                        color_value = bg_style["color"]
                                        if isinstance(color_value, tuple):
                                            bg_style_kwargs["bgcolor"] = (
                                                f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                                            )
                                        else:
                                            bg_style_kwargs["bgcolor"] = color_value
                                    except Exception:
                                        pass
                                panel_kwargs["style"] = Style(**bg_style_kwargs)
                            else:
                                # Handle string or tuple background style
                                if isinstance(bg_style, tuple):
                                    panel_kwargs["style"] = Style(
                                        bgcolor=f"rgb({bg_style[0]},{bg_style[1]},{bg_style[2]})"
                                    )
                                else:
                                    panel_kwargs["style"] = Style(bgcolor=bg_style)
                        except Exception:
                            # Skip background style if processing fails
                            pass

                    # Handle border style
                    if "border_style" in bg_settings:
                        try:
                            border_style = bg_settings["border_style"]
                            if isinstance(border_style, dict):
                                border_style_kwargs = {}
                                if "color" in border_style:
                                    try:
                                        color_value = border_style["color"]
                                        if isinstance(color_value, tuple):
                                            border_style_kwargs["color"] = (
                                                f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                                            )
                                        else:
                                            border_style_kwargs["color"] = color_value
                                    except Exception:
                                        pass

                                for prop in ["bold", "dim", "italic"]:
                                    if prop in border_style:
                                        try:
                                            border_style_kwargs[prop] = border_style[
                                                prop
                                            ]
                                        except Exception:
                                            continue

                                panel_kwargs["border_style"] = Style(
                                    **border_style_kwargs
                                )
                        except Exception:
                            # Skip border style if processing fails
                            pass

                    # Handle background color if specified at top level
                    if "color" in bg_settings and "style" not in bg_settings:
                        try:
                            color_value = bg_settings["color"]
                            if isinstance(color_value, tuple):
                                panel_kwargs["style"] = Style(
                                    bgcolor=f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                                )
                            else:
                                panel_kwargs["style"] = Style(bgcolor=color_value)
                        except Exception:
                            # Skip background color if processing fails
                            pass

                    try:
                        return Panel(styled_renderable, **panel_kwargs)
                    except Exception:
                        # Fallback to styled renderable if panel creation fails
                        return styled_renderable

                elif bg:
                    # Simple background color (string from bg parameter)
                    try:
                        panel_kwargs = {}
                        bg_style = Style(bgcolor=bg)
                        panel_kwargs["style"] = bg_style

                        # Handle direct panel parameters even with simple bg
                        if title is not None:
                            panel_kwargs["title"] = title
                        if padding is not None:
                            panel_kwargs["padding"] = padding
                        if expand is not None:
                            panel_kwargs["expand"] = expand
                        if border is not None:
                            try:
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
                                        rich_box_module,
                                        "MARKDOWN",
                                        rich_box_module.ROUNDED,
                                    ),
                                }
                                panel_kwargs["box"] = box_map.get(
                                    border, rich_box_module.ROUNDED
                                )
                            except Exception:
                                # Use default box if box processing fails
                                pass

                        return Panel(styled_renderable, **panel_kwargs)
                    except Exception:
                        # Fallback to styled renderable if panel creation fails
                        return styled_renderable
                else:
                    # Handle panel parameters without background
                    if (
                        title is not None
                        or padding is not None
                        or expand is not None
                        or border is not None
                    ):
                        try:
                            panel_kwargs = {}

                            if title is not None:
                                panel_kwargs["title"] = title
                            if padding is not None:
                                panel_kwargs["padding"] = padding
                            if expand is not None:
                                panel_kwargs["expand"] = expand
                            if border is not None:
                                try:
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
                                            rich_box_module,
                                            "MARKDOWN",
                                            rich_box_module.ROUNDED,
                                        ),
                                    }
                                    panel_kwargs["box"] = box_map.get(
                                        border, rich_box_module.ROUNDED
                                    )
                                except Exception:
                                    # Use default box if box processing fails
                                    pass

                            return Panel(styled_renderable, **panel_kwargs)
                        except Exception:
                            # Fallback to styled renderable if panel creation fails
                            return styled_renderable
            except Exception:
                # Skip background processing if it fails
                pass

        # Return styled renderable (with or without background processing)
        return styled_renderable

    except Exception:
        # Ultimate fallback - return original renderable
        return r
