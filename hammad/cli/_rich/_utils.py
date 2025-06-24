"""hammad.cli._rich._utils

Contains helper utilities for the rich plugin."""

import logging
import inspect
from typing import Optional, Dict
import time

from rich import get_console as get_rich_console
from rich.text import Text as RichText
from rich.panel import Panel as RichPanel
from rich.style import Style as RichStyle
from rich.console import RenderableType as RichRenderableType
from rich.logging import RichHandler

from ._types import (
    LoggingLevelName,
    RichColorType,
    RichRenderableSettings,
    RichConsole,
    RichLive,
    RichLiveSettings,
    RichLoggingLevelSettings,
    RichLoggingSettings,
    RichDefaultLoggingLevelSettings,
    RichStyleType,
)


__all__ = (
    "wrap_renderable_with_rich_config",
    "get_rich_console",
    "has_rich_handler",
    "create_rich_handler",
    "update_rich_handler",
    "create_rich_logger",
    "update_rich_logger",
    "run_rich_live",
)


class RichPluginError(Exception):
    """Exception raised by the rich plugin."""


class RichLoggingFilter(logging.Filter):
    """Filter for applying rich styling to log messages based on level."""

    def __init__(self, level_settings: Dict[str, RichLoggingLevelSettings]):
        super().__init__()
        self.level_settings = level_settings

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply styling configuration to log record."""
        level_name = record.levelname.lower()

        # Check if we have custom styling for this level
        if level_name in self.level_settings:
            record._hammad_rich_config = self.level_settings[level_name]

        return True


class RichLoggingFormatter(logging.Formatter):
    """Custom formatter that applies rich styling using the new type system."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        validate: bool = True,
        defaults: Optional[Dict[str, any]] = None,
        global_settings: Optional[RichLoggingSettings] = None,
    ):
        # Handle different Python versions - defaults parameter was added in Python 3.8
        try:
            super().__init__(fmt, datefmt, style, validate, defaults)
        except TypeError:
            # Fallback for older Python versions
            super().__init__(fmt, datefmt, style, validate)
        
        self.console = get_rich_console()
        self.global_settings = global_settings or {}

    def formatMessage(self, record: logging.LogRecord) -> str:
        """Override formatMessage to apply styling to different parts."""
        # Get level-specific configuration
        level_config = getattr(record, "_hammad_rich_config", {})

        # Build the formatted message parts
        parts = []

        # Handle name display
        if self.global_settings.get("show_name", True):
            name_part = self._format_logger_name(record, level_config)
            if name_part:
                parts.append(name_part)

        # Handle level display
        if level_config.get("show_level", self.global_settings.get("show_level", True)):
            level_part = self._format_level_name(record, level_config)
            if level_part:
                parts.append(level_part)

        # Handle time display
        if level_config.get("show_time", self.global_settings.get("show_time", False)):
            time_part = self._format_time(record, level_config)
            if time_part:
                parts.append(time_part)

        # Handle message
        message_part = self._format_message(record, level_config)
        if message_part:
            parts.append(message_part)

        # Join parts with separator
        separator = " - "
        formatted_message = separator.join(parts)

        return formatted_message

    def _format_logger_name(
        self, record: logging.LogRecord, level_config: RichLoggingLevelSettings
    ) -> str:
        """Format the logger name with styling."""
        name = record.name

        # Apply prefix if specified in global settings
        if self.global_settings.get("prefix"):
            name = f"{self.global_settings['prefix']}{name}"

        # Apply level-specific or global styling
        style = level_config.get("level_style") or self.global_settings.get("style")
        if style:
            name = self._apply_style_to_text(name, style)

        return name

    def _format_level_name(
        self, record: logging.LogRecord, level_config: RichLoggingLevelSettings
    ) -> str:
        """Format the level name with styling."""
        level_name = record.levelname

        # Apply level-specific styling
        style = level_config.get("level_style")
        if style:
            level_name = self._apply_style_to_text(level_name, style)

        return level_name

    def _format_time(
        self, record: logging.LogRecord, level_config: RichLoggingLevelSettings
    ) -> str:
        """Format the timestamp."""
        if self.datefmt:
            time_str = self.formatTime(record, self.datefmt)
        else:
            time_str = self.formatTime(record)

        return time_str

    def _format_message(
        self, record: logging.LogRecord, level_config: RichLoggingLevelSettings
    ) -> str:
        """Format the log message with styling."""
        message = record.getMessage()

        # Apply message-specific styling
        style = level_config.get("message_style") or level_config.get("style")
        if style:
            message = self._apply_style_to_text(message, style)

        return message

    def _apply_style_to_text(self, text: str, style: RichStyleType) -> str:
        """Apply rich styling to text."""
        if isinstance(style, str):
            # Handle string styles like "bold red" or color names
            # For multi-word styles, we need to close with the full style
            return f"[{style}]{text}[/{style}]"
        elif isinstance(style, dict):
            # Handle RichStyleSettings dict
            return self._build_markup_from_dict(text, style)
        elif isinstance(style, tuple):
            # Handle RGB tuple
            rgb_str = f"rgb({style[0]},{style[1]},{style[2]})"
            return f"[{rgb_str}]{text}[/{rgb_str}]"
        else:
            return text

    def _build_markup_from_dict(self, text: str, style_dict: dict) -> str:
        """Build rich markup from a style dictionary."""
        style_parts = []
        
        # Handle color
        if "color" in style_dict:
            color = style_dict["color"]
            if isinstance(color, tuple):
                style_parts.append(f"rgb({color[0]},{color[1]},{color[2]})")
            else:
                style_parts.append(str(color))
        
        # Handle style attributes
        for attr in [
            "bold",
            "italic",
            "dim",
            "underline",
            "strike",
            "blink",
            "reverse",
            "conceal",
        ]:
            if style_dict.get(attr):
                style_parts.append(attr)
        
        if style_parts:
            style_str = " ".join(style_parts)
            # Use the full style string for both opening and closing tags
            return f"[{style_str}]{text}[/{style_str}]"
        else:
            return text


def has_rich_handler(logger: logging.Logger) -> bool:
    """Check if a logger has a RichHandler."""
    for handler in logger.handlers:
        if isinstance(handler, RichHandler):
            return True
    return False


def create_rich_handler(settings: RichLoggingSettings) -> RichHandler:
    """Create a RichHandler with the specified settings.

    Args:
        settings: Configuration settings for the rich handler

    Returns:
        Configured RichHandler instance
    """
    console = get_rich_console()

    # Extract handler-specific settings
    handler_kwargs = {
        "console": console,
        "rich_tracebacks": True,
        "markup": True,
        "show_time": settings.get("show_time", False),
        "show_path": settings.get("show_path", False),
        "show_level": settings.get("show_level", True),
    }

    # Create the handler
    handler = RichHandler(**handler_kwargs)

    # Create custom formatter
    fmt_string = "| [bold]✼ {name}[/bold] - {message}"
    formatter = RichLoggingFormatter(
        fmt=fmt_string, style="{", global_settings=settings
    )
    handler.setFormatter(formatter)

    # Create and add filter for level-specific styling
    level_settings = {}
    if "levels" in settings:
        level_settings.update(settings["levels"])

    # Merge with defaults
    for level_name, default_config in RichDefaultLoggingLevelSettings.items():
        if level_name not in level_settings:
            level_settings[level_name] = default_config

    # Add filter
    handler.addFilter(RichLoggingFilter(level_settings))

    return handler


def update_rich_handler(
    handler: RichHandler,
    settings: RichLoggingSettings | None = None,
    levels: Dict[LoggingLevelName, RichLoggingLevelSettings] | None = None,
) -> None:
    """Update an existing RichHandler with new settings.

    Args:
        handler: The RichHandler to update
        settings: New global logging settings
        levels: New level-specific settings
    """
    if not isinstance(handler, RichHandler):
        raise RichPluginError("Handler must be a RichHandler instance")

    # Update formatter if settings provided
    if settings:
        fmt_string = "| [bold]✼ {name}[/bold] - {message}"
        formatter = RichLoggingFormatter(
            fmt=fmt_string, style="{", global_settings=settings
        )
        handler.setFormatter(formatter)

    # Update filters
    if settings or levels:
        # Remove existing RichLoggingFilter
        for f in handler.filters[:]:
            if isinstance(f, RichLoggingFilter):
                handler.removeFilter(f)

        # Build new level settings
        level_settings = {}
        if levels:
            level_settings.update(levels)
        elif settings and "levels" in settings:
            level_settings.update(settings["levels"])

        # Merge with defaults
        for level_name, default_config in RichDefaultLoggingLevelSettings.items():
            if level_name not in level_settings:
                level_settings[level_name] = default_config

        # Add new filter
        handler.addFilter(RichLoggingFilter(level_settings))


def create_rich_logger(
    name: str | None = None,
    settings: RichLoggingSettings | None = None,
) -> logging.Logger:
    """Create a new logger with rich formatting.

    Args:
        name: Name for the logger. If None, uses caller's function name
        settings: Configuration settings for the logger

    Returns:
        Configured logger instance
    """
    # Determine logger name
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_code.co_name
        else:
            name = "hammad"

    # Use name from settings if provided
    if settings and settings.get("name"):
        name = settings["name"]

    # Create logger
    logger = logging.getLogger(name)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create and add rich handler
    handler_settings = settings or {}
    handler = create_rich_handler(handler_settings)
    logger.addHandler(handler)

    # Set logger level (default to INFO)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Add custom levels if specified
    if settings and "levels" in settings:
        for level_name, level_config in settings["levels"].items():
            # Check if this is a new custom level (not in standard levels)
            if level_name not in ["debug", "info", "warning", "error", "critical"]:
                # For custom levels, we need a numeric value
                # This is a simplified approach - in practice you'd want to specify the value
                custom_level_value = logging.INFO + 5  # Just an example
                logging.addLevelName(custom_level_value, level_name.upper())

    return logger


def update_rich_logger(
    logger: logging.Logger,
    settings: RichLoggingSettings | None = None,
    levels: Dict[LoggingLevelName, RichLoggingLevelSettings] | None = None,
) -> None:
    """Update an existing logger with new rich settings.

    Args:
        logger: The logger to update
        settings: New global logging settings
        levels: New level-specific settings
    """
    # Find and update rich handlers
    rich_handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]

    if not rich_handlers:
        # No rich handler exists, create one
        if settings:
            handler = create_rich_handler(settings)
            logger.addHandler(handler)
    else:
        # Update existing rich handlers
        for handler in rich_handlers:
            update_rich_handler(handler, settings, levels)

    # Add custom levels if specified
    if settings and "levels" in settings:
        for level_name, level_config in settings["levels"].items():
            if level_name not in ["debug", "info", "warning", "error", "critical"]:
                # For custom levels, we need a numeric value
                custom_level_value = logging.INFO + 5  # Simplified approach
                logging.addLevelName(custom_level_value, level_name.upper())


def run_rich_live(
    r: RichRenderableType,
    settings: RichLiveSettings,
    console: Optional[RichConsole] = get_rich_console(),
) -> None:
    """Runs a rich live renderable.

    Args:
        r : The renderable to run.
        settings : The settings to use for the live renderable.
        console : The console to use for the live renderable."""

    if not isinstance(r, RichRenderableType):
        raise RichPluginError("The renderable must be a RichRenderableType.")

    if not settings.get("duration"):
        duration = 2.0
    else:
        duration = settings["duration"]
    del settings["duration"]

    if not settings.get("refresh_rate"):
        refresh_rate = 20
    else:
        refresh_rate = settings["refresh_rate"]
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
        with RichLive(r, console=console, **settings) as live:
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1 / refresh_rate)
                live.refresh()
    except Exception as e:
        raise RichPluginError(f"Error running rich live: {e}") from e


def wrap_renderable_with_rich_config(
    r: RichRenderableType,
    style: RichColorType | RichRenderableSettings,
) -> RichRenderableType:
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
        # Handle string-based styles (including color tags and complex styles)
        if isinstance(style, str):
            try:
                # For strings, use Rich's style parsing directly to support things like 'black on red'
                rich_style = RichStyle.parse(style)
                styled_renderable = (
                    RichText(r, style=rich_style) if isinstance(r, str) else r
                )
                return styled_renderable
            except Exception:
                # Fallback to treating as simple color if parsing fails
                rich_style = RichStyle(color=style)
                styled_renderable = (
                    RichText(r, style=rich_style) if isinstance(r, str) else r
                )
                return styled_renderable

        # Handle tuple colors
        elif isinstance(style, tuple):
            try:
                color_string = f"rgb({style[0]},{style[1]},{style[2]})"
                rich_style = RichStyle(color=color_string)
                styled_renderable = (
                    RichText(r, style=rich_style) if isinstance(r, str) else r
                )
                return styled_renderable
            except Exception:
                # Fallback to no styling if tuple processing fails
                return r

        # Handle RichRenderableSettings dict
        elif isinstance(style, dict):
            try:
                # Extract background settings if present
                background_settings = style.get("background")

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
                        RichStyle(**text_style_kwargs) if text_style_kwargs else None
                    )
                except Exception:
                    rich_style = None

                # Apply text style to renderable
                try:
                    if isinstance(r, str):
                        styled_renderable = (
                            RichText(r, style=rich_style) if rich_style else RichText(r)
                        )
                    elif isinstance(r, RichText) and rich_style:
                        styled_renderable = RichText(r.plain, style=rich_style)
                    else:
                        styled_renderable = r
                except Exception:
                    styled_renderable = r

                # Handle background settings
                if background_settings:
                    try:
                        if isinstance(background_settings, dict):
                            # Full background configuration
                            panel_kwargs = {}

                            # Handle box style
                            if "box" in background_settings:
                                try:
                                    box_name = background_settings["box"]
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
                                if prop in background_settings:
                                    try:
                                        panel_kwargs[prop] = background_settings[prop]
                                    except Exception:
                                        # Skip property if processing fails
                                        continue

                            # Handle background style
                            if "style" in background_settings:
                                try:
                                    bg_style = background_settings["style"]
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
                                                    bg_style_kwargs["bgcolor"] = (
                                                        color_value
                                                    )
                                            except Exception:
                                                pass
                                        panel_kwargs["style"] = RichStyle(
                                            **bg_style_kwargs
                                        )
                                    else:
                                        # Handle string or tuple background style
                                        if isinstance(bg_style, tuple):
                                            panel_kwargs["style"] = RichStyle(
                                                bgcolor=f"rgb({bg_style[0]},{bg_style[1]},{bg_style[2]})"
                                            )
                                        else:
                                            panel_kwargs["style"] = RichStyle(
                                                bgcolor=bg_style
                                            )
                                except Exception:
                                    # Skip background style if processing fails
                                    pass

                            # Handle border style
                            if "border_style" in background_settings:
                                try:
                                    border_style = background_settings["border_style"]
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
                                                    border_style_kwargs["color"] = (
                                                        color_value
                                                    )
                                            except Exception:
                                                pass

                                        for prop in ["bold", "dim", "italic"]:
                                            if prop in border_style:
                                                try:
                                                    border_style_kwargs[prop] = (
                                                        border_style[prop]
                                                    )
                                                except Exception:
                                                    continue

                                        panel_kwargs["border_style"] = RichStyle(
                                            **border_style_kwargs
                                        )
                                except Exception:
                                    # Skip border style if processing fails
                                    pass

                            # Handle background color if specified at top level
                            if (
                                "color" in background_settings
                                and "style" not in background_settings
                            ):
                                try:
                                    color_value = background_settings["color"]
                                    if isinstance(color_value, tuple):
                                        panel_kwargs["style"] = RichStyle(
                                            bgcolor=f"rgb({color_value[0]},{color_value[1]},{color_value[2]})"
                                        )
                                    else:
                                        panel_kwargs["style"] = RichStyle(
                                            bgcolor=color_value
                                        )
                                except Exception:
                                    # Skip background color if processing fails
                                    pass

                            try:
                                return RichPanel(styled_renderable, **panel_kwargs)
                            except Exception:
                                # Fallback to styled renderable if panel creation fails
                                return styled_renderable

                        else:
                            # Simple background color (string or tuple)
                            try:
                                if isinstance(background_settings, tuple):
                                    bg_style = RichStyle(
                                        bgcolor=f"rgb({background_settings[0]},{background_settings[1]},{background_settings[2]})"
                                    )
                                else:
                                    bg_style = RichStyle(bgcolor=background_settings)

                                return RichPanel(styled_renderable, style=bg_style)
                            except Exception:
                                # Fallback to styled renderable if panel creation fails
                                return styled_renderable
                    except Exception:
                        # Skip background processing if it fails
                        pass

                # No background, just return styled renderable
                return styled_renderable

            except Exception:
                # Fallback to original renderable if dict processing fails
                return r

        # Fallback for unexpected types
        return r

    except Exception:
        # Ultimate fallback - return original renderable
        return r
