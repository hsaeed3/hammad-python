"""hammad.logging.logger"""

import logging as _logging
import inspect
from dataclasses import dataclass, field
from typing import (
    Literal,
    TypeAlias,
    NamedTuple,
    ParamSpec,
    TypeVar,
    Dict,
    Optional,
    Any,
    Union,
)
from typing_extensions import TypedDict

from rich import get_console as get_rich_console
from rich.logging import RichHandler

from ..cli.styles.types import (
    CLIStyleType,
)
from ..cli.styles.settings import CLIStyleRenderableSettings, CLIStyleBackgroundSettings

__all__ = (
    "Logger",
    "create_logger",
    "create_logger_level",
)


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------


LoggerLevelName: TypeAlias = Literal["debug", "info", "warning", "error", "critical"]
"""Literal type helper for logging levels."""


_P = ParamSpec("_P")
_R = TypeVar("_R")


class LoggerLevelSettings(TypedDict, total=False):
    """Configuration dictionary for the display style of a
    single logging level."""

    title: CLIStyleType | CLIStyleRenderableSettings
    """Either a string tag or style settings for the title output
    of the messages of this level. This includes module name
    and level name."""

    message: CLIStyleType | CLIStyleRenderableSettings
    """Either a string tag or style settings for the message output
    of the messages of this level. This includes the message itself."""

    background: CLIStyleType | CLIStyleBackgroundSettings
    """Either a string tag or style settings for the background output
    of the messages of this level. This includes the message itself."""


# -----------------------------------------------------------------------------
# Default Level Styles
# -----------------------------------------------------------------------------

DEFAULT_LEVEL_STYLES: Dict[str, LoggerLevelSettings] = {
    "critical": {
        "message": "red bold",
    },
    "error": {
        "message": "red italic",
    },
    "warning": {
        "message": "yellow italic",
    },
    "info": {
        "message": "white",
    },
    "debug": {
        "message": "white italic dim",
    },
}


# -----------------------------------------------------------------------------
# Logging Filter
# -----------------------------------------------------------------------------


class RichLoggerFilter(_logging.Filter):
    """Filter for applying rich styling to log messages based on level."""

    def __init__(self, level_styles: Dict[str, LoggerLevelSettings]):
        super().__init__()
        self.level_styles = level_styles

    def filter(self, record: _logging.LogRecord) -> bool:
        # Get the level name
        level_name = record.levelname.lower()

        # Check if we have custom styling for this level
        if level_name in self.level_styles:
            style_config = self.level_styles[level_name]

            # We'll use a special attribute to store style config
            # The formatter/handler will use this to apply styling
            record._hammad_style_config = style_config

        return True


# -----------------------------------------------------------------------------
# Custom Rich Formatter
# -----------------------------------------------------------------------------


class RichLoggerFormatter(_logging.Formatter):
    """Custom formatter that applies rich styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = get_rich_console()

    def formatMessage(self, record: _logging.LogRecord) -> str:
        """Override formatMessage to apply styling to different parts."""
        # Check if we have style configuration
        if hasattr(record, "_hammad_style_config"):
            style_config = record._hammad_style_config

            # Handle title styling (logger name)
            title_style = style_config.get("title", None)
            if title_style:
                if isinstance(title_style, str):
                    # It's a color/style string tag
                    record.name = f"[{title_style}]{record.name}[/{title_style}]"
                elif isinstance(title_style, dict):
                    # It's a CLIStyleRenderableSettings dict
                    style_str = self._build_renderable_style_string(title_style)
                    if style_str:
                        record.name = f"[{style_str}]{record.name}[/{style_str}]"

            # Handle message styling
            message_style = style_config.get("message", None)
            if message_style:
                if isinstance(message_style, str):
                    # It's a color/style string tag
                    record.message = (
                        f"[{message_style}]{record.getMessage()}[/{message_style}]"
                    )
                elif isinstance(message_style, dict):
                    # It's a CLIStyleRenderableSettings dict
                    style_str = self._build_renderable_style_string(message_style)
                    if style_str:
                        record.message = (
                            f"[{style_str}]{record.getMessage()}[/{style_str}]"
                        )
                else:
                    record.message = record.getMessage()
            else:
                record.message = record.getMessage()
        else:
            record.message = record.getMessage()

        # Now format with the styled values
        return self._style._fmt.format(**record.__dict__)

    def _build_renderable_style_string(self, style_dict: dict) -> str:
        """Build a rich markup style string from a CLIStyleRenderableSettings dictionary."""
        style_parts = []

        # Handle all the style attributes from CLIStyleRenderableSettings
        for attr in [
            "bold",
            "italic",
            "dim",
            "underline",
            "strike",
            "blink",
            "blink2",
            "reverse",
            "conceal",
            "underline2",
            "frame",
            "encircle",
            "overline",
        ]:
            if style_dict.get(attr):
                style_parts.append(attr)

        return " ".join(style_parts) if style_parts else ""


# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------


@dataclass
class Logger:
    """Flexible logger with rich styling and custom level support."""

    _logger: _logging.Logger = field(init=False)
    """The underlying logging.Logger instance."""

    _level_styles: Dict[str, LoggerLevelSettings] = field(init=False)
    """Custom level styles."""

    _custom_levels: Dict[str, int] = field(init=False)
    """Custom logging levels."""

    _user_level: str = field(init=False)
    """User-specified logging level."""

    def __init__(
        self,
        name: Optional[str] = None,
        level: Optional[Union[str, int]] = None,
        rich: bool = True,
        display_all: bool = False,
        level_styles: Optional[Dict[str, LoggerLevelSettings]] = None,
    ) -> None:
        """
        Initialize a new Logger instance.

        Args:
            name: Name for the logger. If None, defaults to "hammad"
            level: Logging level. If None, defaults to "debug" if display_all else "warning"
            rich: Whether to use rich formatting for output
            display_all: If True, sets effective level to debug to show all messages
            level_styles: Custom level styles to override defaults
        """
        logger_name = name or "hammad"

        # Initialize custom levels dict
        self._custom_levels = {}

        # Initialize level styles with defaults
        self._level_styles = DEFAULT_LEVEL_STYLES.copy()
        if level_styles:
            self._level_styles.update(level_styles)

        # Handle integer levels by converting to string names
        if isinstance(level, int):
            # Map standard logging levels to their names
            int_to_name = {
                _logging.DEBUG: "debug",
                _logging.INFO: "info",
                _logging.WARNING: "warning",
                _logging.ERROR: "error",
                _logging.CRITICAL: "critical",
            }
            level = int_to_name.get(level, "warning")

        self._user_level = level or "warning"

        if display_all:
            effective_level = "debug"
        else:
            effective_level = self._user_level

        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Check if it's a custom level
        if effective_level.lower() in self._custom_levels:
            log_level = self._custom_levels[effective_level.lower()]
        else:
            log_level = level_map.get(effective_level.lower(), _logging.WARNING)

        # Create logger
        self._logger = _logging.getLogger(logger_name)

        # Clear any existing handlers
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        # Setup handler based on rich preference
        if rich:
            self._setup_rich_handler(log_level)
        else:
            self._setup_standard_handler(log_level)

        self._logger.setLevel(log_level)
        self._logger.propagate = False

    def _setup_rich_handler(self, log_level: int) -> None:
        """Setup rich handler for the logger."""
        console = get_rich_console()

        handler = RichHandler(
            level=log_level,
            console=console,
            rich_tracebacks=True,
            show_time=False,
            show_path=False,
            markup=True,
        )

        formatter = RichLoggerFormatter(
            "| [bold]✼ {name}[/bold] - {message}", style="{"
        )
        handler.setFormatter(formatter)

        # Add our custom filter
        handler.addFilter(RichLoggerFilter(self._level_styles))

        self._logger.addHandler(handler)

    def _setup_standard_handler(self, log_level: int) -> None:
        """Setup standard handler for the logger."""
        handler = _logging.StreamHandler()
        formatter = _logging.Formatter("✼  {name} - {levelname} - {message}", style="{")
        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        self._logger.addHandler(handler)

    def add_level(
        self, name: str, value: int, style: Optional[LoggerLevelSettings] = None
    ) -> None:
        """
        Add a custom logging level.

        Args:
            name: Name of the custom level
            value: Numeric value for the level (should be unique)
            style: Optional style settings for the level
        """
        # Add to Python's logging module
        _logging.addLevelName(value, name.upper())

        # Store in our custom levels
        self._custom_levels[name.lower()] = value

        # Add style if provided
        if style:
            self._level_styles[name.lower()] = style

        # Update filters if using rich handler
        for handler in self._logger.handlers:
            if isinstance(handler, RichHandler):
                # Remove old filter and add new one with updated styles
                for f in handler.filters[:]:
                    if isinstance(f, RichLoggerFilter):
                        handler.removeFilter(f)
                handler.addFilter(RichLoggerFilter(self._level_styles))

    @property
    def level(self) -> str:
        """Get the current logging level."""
        return self._user_level

    @level.setter
    def level(self, value: str) -> None:
        """Set the logging level."""
        self._user_level = value

        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Check custom levels
        if value.lower() in self._custom_levels:
            log_level = self._custom_levels[value.lower()]
        else:
            log_level = level_map.get(value.lower(), _logging.WARNING)

        # Update logger level
        self._logger.setLevel(log_level)

        # Update handler levels
        for handler in self._logger.handlers:
            handler.setLevel(log_level)

    # Convenience methods for standard logging levels
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def log(
        self, level: Union[str, int], message: str, *args: Any, **kwargs: Any
    ) -> None:
        """
        Log a message at the specified level.

        Args:
            level: The level to log at (can be standard or custom)
            message: The message to log
            *args: Additional positional arguments for the logger
            **kwargs: Additional keyword arguments for the logger
        """
        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Handle integer levels
        if isinstance(level, int):
            # Use the integer level directly
            log_level = level
        else:
            # Check custom levels first
            if level.lower() in self._custom_levels:
                log_level = self._custom_levels[level.lower()]
            else:
                log_level = level_map.get(level.lower(), _logging.WARNING)

        self._logger.log(log_level, message, *args, **kwargs)

    @property
    def name(self) -> str:
        """Get the logger name."""
        return self._logger.name

    @property
    def handlers(self) -> list[_logging.Handler]:
        """Get the logger handlers."""
        return self._logger.handlers

    def get_logger(self) -> _logging.Logger:
        """Get the underlying logging.Logger instance."""
        return self._logger


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def create_logger_level(
    name: str,
    level: int,
    color: Optional[str] = None,
    style: Optional[str] = None,
) -> None:
    """
    Create a custom logging level.

    Args:
        name: The name of the logging level (e.g., "TRACE", "SUCCESS")
        level: The numeric level value (should be between existing levels)
        color: Optional color for rich formatting (e.g., "green", "blue")
        style: Optional style for rich formatting (e.g., "bold", "italic")
    """
    # Convert name to uppercase for consistency
    level_name = name.upper()

    # Add the level to the logging module
    _logging.addLevelName(level, level_name)

    # Create a method on the Logger class for this level
    def log_method(self, message, *args, **kwargs):
        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    # Add the method to the standard logging.Logger class
    setattr(_logging.Logger, name.lower(), log_method)

    # Store level info for potential rich formatting
    if hasattr(_logging, "_custom_level_info"):
        _logging._custom_level_info[level] = {
            "name": level_name,
            "color": color,
            "style": style,
        }
    else:
        _logging._custom_level_info = {
            level: {"name": level_name, "color": color, "style": style}
        }


def create_logger(
    name: Optional[str] = None,
    level: Optional[Union[str, int]] = None,
    rich: bool = True,
    display_all: bool = False,
    levels: Optional[Dict[LoggerLevelName, LoggerLevelSettings]] = None,
) -> Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger. If None, uses caller's function name
        level: Logging level. If None, defaults to "debug" if display_all else "warning"
        rich: Whether to use rich formatting for output
        display_all: If True, sets effective level to debug to show all messages
        levels: Custom level styles to override defaults. Also can contain
        custom levels.

    Returns:
        A Logger instance with the specified configuration.
    """
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_code.co_name
        else:
            name = "logger"

    return Logger(name, level, rich, display_all, level_styles=levels)
