"""hammad._internal._style_utils"""

import time
from typing import Optional
from rich import get_console
from rich.console import Console, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from ._style_types import (
    StyleError,
    StyleLiveSettings,
    StyleStyleSettings,
    StyleBackgroundSettings,
    StyleColorName,
)

__all__ = (
    "live_render",
    "wrap_renderable_with_styles",
)


def live_render(
    r: RenderableType,
    settings: StyleLiveSettings,
    console: Optional[Console] = get_console(),
) -> None:
    """Runs a rich live renderable.

    Args:
        r : The renderable to run.
        settings : The settings to use for the live renderable.
        console : The console to use for the live renderable."""

    if not isinstance(r, RenderableType):
        raise StyleError("The renderable must be a RenderableType.")

    if not settings.get("duration"):
        duration = 2.0
    else:
        duration = settings["duration"]
    if "duration" in settings:
        del settings["duration"]

    if not settings.get("refresh_rate"):
        refresh_rate = 20
    else:
        refresh_rate = settings["refresh_rate"]
    if "refresh_rate" in settings:
        del settings["refresh_rate"]

    if not settings.get("auto_refresh"):
        settings["auto_refresh"] = True
    if not settings.get("transient"):
        settings["transient"] = False
    if not settings.get("redirect_stdout"):
        settings["redirect_stdout"] = True
    if not settings.get("redirect_stderr"):
        settings["redirect_stderr"] = True
    if not settings.get("vertical_overflow"):
        settings["vertical_overflow"] = "ellipsis"

    try:
        with Live(r, console=console, **settings) as live:
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1 / refresh_rate)
                live.refresh()
    except Exception as e:
        raise StyleError(f"Error running rich live: {e}") from e


def wrap_renderable_with_styles(
    r: RenderableType,
    style: StyleColorName | StyleStyleSettings | None = None,
    background: StyleBackgroundSettings | None = None,
) -> RenderableType:
    """Wraps a renderable with rich configuration.

    Args:
        r : The renderable to wrap.
        style : The style to apply to the renderable. Can be:
            - A color name/hex/tuple for simple color styling
            - A style string like 'bold red on blue' for complex styling
            - A RichRenderableSettings dict for full configuration

    Returns:
        The wrapped renderable."""

    try:
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

        # Handle tuple colors
        elif isinstance(style, tuple):
            try:
                color_string = f"rgb({style[0]},{style[1]},{style[2]})"
                rich_style = Style(color=color_string)
                styled_renderable = (
                    Text(r, style=rich_style) if isinstance(r, str) else r
                )
            except Exception:
                # Fallback to no styling if tuple processing fails
                styled_renderable = r

        # Handle PrintStyleSettings dict
        elif isinstance(style, dict):
            try:
                # Process text/style properties
                text_style_kwargs = {}

                # Handle color from style settings
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

        # Handle background settings (from separate background parameter)
        if background:
            try:
                if isinstance(background, dict):
                    # Full background configuration
                    panel_kwargs = {}

                    # Handle box style
                    if "box" in background:
                        try:
                            box_name = background["box"]
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
                        if prop in background:
                            try:
                                panel_kwargs[prop] = background[prop]
                            except Exception:
                                # Skip property if processing fails
                                continue

                    # Handle background style
                    if "style" in background:
                        try:
                            bg_style = background["style"]
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
                    if "border_style" in background:
                        try:
                            border_style = background["border_style"]
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
                    if "color" in background and "style" not in background:
                        try:
                            color_value = background["color"]
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

                else:
                    # Simple background color (string or tuple)
                    try:
                        if isinstance(background, tuple):
                            bg_style = Style(
                                bgcolor=f"rgb({background[0]},{background[1]},{background[2]})"
                            )
                        else:
                            bg_style = Style(bgcolor=background)

                        return Panel(styled_renderable, style=bg_style)
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
