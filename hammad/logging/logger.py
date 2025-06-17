"""hammad.logging.logger"""

from dataclasses import dataclass, field
import logging
import inspect
from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict, NotRequired

from ..plugins.rich import (
    create_rich_logger,
    update_rich_logger,
    RichLoggingLevelSettings,
    RichLoggingSettings,
    RichStyleType,
    RichBackgroundType
)
from ..plugins.rich._types import LoggingLevelName


class LoggerLevelSettings(TypedDict, total=False):
    """Configuration dictionary for the display style of a
    single logging level."""
    
    before_level: NotRequired[str | RichStyleType]
    """The level in which this level is *stronger* than. This is only
    applicable to custom levels."""

    after_level: NotRequired[str | RichStyleType]
    """The level in which this level is *weaker* than. This is only
    applicable to custom levels."""


class LoggerSettings(RichLoggingSettings):
    """Helper configuration dictionary used to define the 'logger'
    of various renderable components. This extends settings found within
    rich.logging."""

    display_all: NotRequired[bool]
    """Whether to **DISPLAY** all messages, regardless of level. This does not mean
    that the logger will log all messages, it will only display them.

    This is useful for debugging or when you want to see all messages, but not make
    any active logging decisions.
    """


@dataclass
class Logger:
    """
    `hammad.logging.Logger`

    An incredibly versatile (opinionated) and styled logger that utilizes
    rich to provide pretty, customizable logging messages within the terminal, with
    support for customization over:

    - Level Styling & Background
    - Adding Custom Levels Easily
    - & More
    """

    _logger: logging.Logger = field(init=False)
    """The underlying logging.Logger instance."""

    _levels: Dict[LoggingLevelName | str, RichLoggingLevelSettings] = field(init=False)
    """Custom levels and their settings."""

    _custom_levels: Dict[str, int] = field(init=False)
    """Custom levels and their numeric values."""

    _user_level: str = field(init=False)
    """User-specified logging level. This is used to support the custom levels."""

    _settings: RichLoggingSettings = field(init=False)
    """Rich logging settings for the logger."""

    def __init__(
        self,
        name: Optional[str] = None,
        level: Optional[str | LoggingLevelName] = None,
        levels: Optional[Dict[LoggingLevelName | str, RichLoggingLevelSettings]] = None,
        style: Optional[RichStyleType] = None,
        bg: Optional[RichBackgroundType] = None,
        display_all: Optional[bool] = False,
        prefix: Optional[str] = None,
        show_time: Optional[bool] = False,
        show_path: Optional[bool] = False,
        show_level: Optional[bool] = True,
        show_name: Optional[bool] = True,
    ) -> None:
        """
        Initialize a new Logger instance.

        Args:
            name: The name of the logger. If None, defaults to "hammad"
            level: The logging level. If None, defaults to "debug" if display_all else "info"
            levels: A dictionary of custom levels and their settings.
            style: The style of the logger.
            bg: The background of the logger.
            display_all: Whether to display all messages, regardless of level.
            prefix: A prefix to add before the logger's name.
            show_time: Whether to show timestamps in log messages.
            show_path: Whether to show the file path in log messages.
            show_level: Whether to show the log level in messages.
            show_name: Whether to show the logger name in messages.
        """
        # Initialize internal state
        self._custom_levels = {}
        self._levels = {}
        
        # Determine logger name
        if name is None:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                name = frame.f_back.f_code.co_name
            else:
                name = "hammad"
        
        # Determine logging level
        if display_all:
            effective_level = "debug"
        else:
            effective_level = level or "info"
        
        self._user_level = effective_level
        
        # Build rich logging settings
        self._settings: RichLoggingSettings = {
            "name": name,
            "show_time": show_time,
            "show_path": show_path,
            "show_level": show_level,
            "show_name": show_name,
        }
        
        # Add optional settings
        if prefix:
            self._settings["prefix"] = prefix
        if style:
            self._settings["style"] = style
        if bg:
            self._settings["background"] = bg
        if levels:
            self._settings["levels"] = levels
            self._levels.update(levels)
        
        # Create the rich logger
        self._logger = create_rich_logger(name, self._settings)
        
        # Set the logging level
        self.level = effective_level
        
        # Store custom levels for later reference
        if levels:
            for level_name, level_config in levels.items():
                if level_name not in ["debug", "info", "warning", "error", "critical"]:
                    # This is a custom level - we need to assign it a numeric value
                    # For now, use a simple approach (in practice, you'd want more control)
                    custom_value = self._get_custom_level_value(level_name)
                    self._custom_levels[level_name.lower()] = custom_value
                    logging.addLevelName(custom_value, level_name.upper())

    def _get_custom_level_value(self, level_name: str) -> int:
        """Get a numeric value for a custom level."""
        # Simple approach: assign values between standard levels
        # In practice, you might want more sophisticated level management
        base_levels = {
            "debug": logging.DEBUG,      # 10
            "info": logging.INFO,        # 20
            "warning": logging.WARNING,  # 30
            "error": logging.ERROR,      # 40
            "critical": logging.CRITICAL # 50
        }
        
        # For now, just assign custom levels between INFO and WARNING
        return logging.INFO + 5  # 25

    @property
    def name(self) -> str:
        """Get the logger name."""
        return self._logger.name

    @property
    def level(self) -> str:
        """Get the current logging level."""
        return self._user_level

    @level.setter
    def level(self, value: str) -> None:
        """Set the logging level."""
        self._user_level = value.lower()
        
        # Standard level mapping
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        
        # Check if it's a custom level
        if self._user_level in self._custom_levels:
            log_level = self._custom_levels[self._user_level]
        else:
            log_level = level_map.get(self._user_level, logging.INFO)
        
        # Update logger and handlers
        self._logger.setLevel(log_level)
        for handler in self._logger.handlers:
            handler.setLevel(log_level)

    def add_level(
        self,
        name: str,
        value: Optional[int] = None,
        style: Optional[RichLoggingLevelSettings] = None,
    ) -> None:
        """
        Add a custom logging level.

        Args:
            name: Name of the custom level
            value: Numeric value for the level. If None, auto-assigns
            style: Optional style settings for the level
        """
        level_name = name.lower()
        
        # Determine numeric value
        if value is None:
            value = self._get_custom_level_value(name)
        
        # Add to Python's logging module
        logging.addLevelName(value, name.upper())
        
        # Store in our custom levels
        self._custom_levels[level_name] = value
        
        # Add style if provided
        if style:
            self._levels[level_name] = style
            
            # Update the logger's settings
            if "levels" not in self._settings:
                self._settings["levels"] = {}
            self._settings["levels"][level_name] = style
            
            # Update the rich logger
            update_rich_logger(self._logger, self._settings)

    def update_level_style(
        self,
        level: str | LoggingLevelName,
        style: RichLoggingLevelSettings,
    ) -> None:
        """
        Update the style for a specific logging level.

        Args:
            level: The level to update
            style: New style settings for the level
        """
        level_name = level.lower()
        self._levels[level_name] = style
        
        # Update the logger's settings
        if "levels" not in self._settings:
            self._settings["levels"] = {}
        self._settings["levels"][level_name] = style
        
        # Update the rich logger
        update_rich_logger(self._logger, self._settings)

    def update_settings(self, settings: RichLoggingSettings) -> None:
        """
        Update the logger's global settings.

        Args:
            settings: New settings to apply
        """
        # Merge with existing settings
        self._settings.update(settings)
        
        # Update the rich logger
        update_rich_logger(self._logger, self._settings)

    # Standard logging methods
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

    def log(self, level: str | int, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a message at the specified level.

        Args:
            level: The level to log at (can be standard, custom name, or numeric)
            message: The message to log
            *args: Additional positional arguments for the logger
            **kwargs: Additional keyword arguments for the logger
        """
        if isinstance(level, str):
            level_name = level.lower()
            
            # Standard level mapping
            level_map = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warning": logging.WARNING,
                "error": logging.ERROR,
                "critical": logging.CRITICAL,
            }
            
            # Check custom levels first
            if level_name in self._custom_levels:
                log_level = self._custom_levels[level_name]
            else:
                log_level = level_map.get(level_name, logging.INFO)
        else:
            log_level = level
        
        self._logger.log(log_level, message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        self._logger.exception(message, *args, **kwargs)

    def get_logger(self) -> logging.Logger:
        """Get the underlying logging.Logger instance."""
        return self._logger

    @property
    def handlers(self) -> List[logging.Handler]:
        """Get the logger handlers."""
        return list(self._logger.handlers)

    def add_handler(self, handler: logging.Handler) -> None:
        """Add a handler to the logger."""
        self._logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler) -> None:
        """Remove a handler from the logger."""
        self._logger.removeHandler(handler)

    def set_level(self, level: str | int) -> None:
        """Set the logging level (alternative to the level property)."""
        if isinstance(level, int):
            self._logger.setLevel(level)
            # Find the level name for internal tracking
            for name, value in {**self._custom_levels, 
                              "debug": logging.DEBUG,
                              "info": logging.INFO,
                              "warning": logging.WARNING,
                              "error": logging.ERROR,
                              "critical": logging.CRITICAL}.items():
                if value == level:
                    self._user_level = name
                    break
        else:
            self.level = level

    def is_enabled_for(self, level: str | int) -> bool:
        """Check if the logger is enabled for the given level."""
        if isinstance(level, str):
            level_name = level.lower()
            if level_name in self._custom_levels:
                level_value = self._custom_levels[level_name]
            else:
                level_map = {
                    "debug": logging.DEBUG,
                    "info": logging.INFO,
                    "warning": logging.WARNING,
                    "error": logging.ERROR,
                    "critical": logging.CRITICAL,
                }
                level_value = level_map.get(level_name, logging.INFO)
        else:
            level_value = level
        
        return self._logger.isEnabledFor(level_value)


def get_logger(
    name: Optional[str] = None,
    level: Optional[str | LoggingLevelName] = None,
    levels: Optional[Dict[LoggingLevelName | str, RichLoggingLevelSettings]] = None,
    style: Optional[RichStyleType] = None,
    bg: Optional[RichBackgroundType] = None,
    display_all: Optional[bool] = False,
    prefix: Optional[str] = None,
    show_time: Optional[bool] = False,
    show_path: Optional[bool] = False,
    show_level: Optional[bool] = True,
    show_name: Optional[bool] = True,
) -> Logger:
    """
    Create and return a new Logger instance.

    This is a convenience function that creates a Logger with the specified
    configuration.

    Args:
        name: The name of the logger. If None, defaults to caller's function name
        level: The logging level. If None, defaults to "debug" if display_all else "info"
        levels: A dictionary of custom levels and their settings
        style: The style of the logger
        bg: The background of the logger
        display_all: Whether to display all messages, regardless of level
        prefix: A prefix to add before the logger's name
        show_time: Whether to show timestamps in log messages
        show_path: Whether to show the file path in log messages
        show_level: Whether to show the log level in messages
        show_name: Whether to show the logger name in messages

    Returns:
        A configured Logger instance
    """
    return Logger(
        name=name,
        level=level,
        levels=levels,
        style=style,
        bg=bg,
        display_all=display_all,
        prefix=prefix,
        show_time=show_time,
        show_path=show_path,
        show_level=show_level,
        show_name=show_name,
    )
    