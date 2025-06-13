"""✼ hammadpy.objects.logger

Contains the `Logger` class, allowing for easy logging configuration and
usage with either standard logging or through the `rich` library."""

from dataclasses import dataclass
import inspect
import logging
from typing import Literal, TypeAlias

from rich import get_console as _get_console
from rich.logging import RichHandler

from .types.color import Color, ColorName

__all__ = ["Logger", "LoggerLevel", "get_logger"]


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------


LoggerLevel: TypeAlias = Literal["debug", "info", "warning", "error", "critical"]
"""Literal type helper for logging levels."""


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


class RichLoggerFilter(logging.Filter):
    """Filter for using rich's markup tags for logging messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.CRITICAL:
            record.msg = f"[bold red]{record.msg}[/bold red]"
        elif record.levelno >= logging.ERROR:
            record.msg = f"[italic red]{record.msg}[/italic red]"
        elif record.levelno >= logging.WARNING:
            record.msg = f"[italic yellow]{record.msg}[/italic yellow]"
        elif record.levelno >= logging.INFO:
            record.msg = f"[white]{record.msg}[/white]"
        elif record.levelno >= logging.DEBUG:
            record.msg = f"[italic dim white]{record.msg}[/italic dim white]"
        return True


# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------


@dataclass
class Logger:
    """
    Quite flexible and easy to use logger with rich styling and simple level
    configuration / management.

    NOTE: By default the `display_all` parameter is set to `False` which will
    display messages at the effective level.
    """

    _logger: logging.Logger | None = None
    """The underlying logging.Logger instance."""

    def __init__(
        self,
        name: str | None = None,
        level: LoggerLevel | None = None,
        rich: bool = True,
        display_all: bool = False,
    ) -> None:
        """
        Initialize a new Logger instance.

        Args:
            name: Name for the logger. If None, defaults to "hammadpy"
            level: Logging level. If None, defaults to "debug" if display_all else "warning"
            rich: Whether to use rich formatting for output
            display_all: If True, sets effective level to debug to show all messages
        """
        logger_name = name or "hammadpy"

        self._user_level = level or "warning"

        if display_all:
            effective_level = "debug"
        else:
            effective_level = self._user_level

        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        log_level = level_map.get(effective_level.lower(), logging.WARNING)

        # Create logger
        self._logger = logging.getLogger(logger_name)

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
        console = _get_console()

        handler = RichHandler(
            level=log_level,
            console=console,
            rich_tracebacks=True,
            show_time=False,
            show_path=False,
            markup=True,
        )
        formatter = logging.Formatter("| [bold]✼ {name}[/bold] - {message}", style="{")
        handler.setFormatter(formatter)
        handler.addFilter(RichLoggerFilter())

        self._logger.addHandler(handler)

    def _setup_standard_handler(self, log_level: int) -> None:
        """Setup standard handler for the logger."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter("✼  {name} - {levelname} - {message}", style="{")
        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        self._logger.addHandler(handler)

    @property
    def handlers(self) -> list[logging.Handler]:
        if not self._logger:
            return []
        return self._logger.handlers

    @handlers.setter
    def handlers(self, value: list[logging.Handler]) -> None:
        if not self._logger:
            return
        self._logger.handlers = value

    @property
    def level(self) -> LoggerLevel:
        if not self._logger:
            return "warning"

        # Return the user-specified level, not the effective level
        return getattr(self, "_user_level", "warning")

    @level.setter
    def level(self, value: LoggerLevel) -> None:
        if not self._logger:
            return

        # Update the user-specified level
        self._user_level = value

        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }

        log_level = level_map.get(value.lower(), logging.WARNING)

        # Update logger level
        self._logger.setLevel(log_level)

        # Update handler levels
        if self.handlers:
            for handler in self.handlers:
                handler.setLevel(log_level)

    # Convenience methods for logging
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        if self._logger:
            self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        if self._logger:
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        if self._logger:
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message."""
        if self._logger:
            self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log a critical message."""
        if self._logger:
            self._logger.critical(message, *args, **kwargs)

    def log(self, level: LoggerLevel, message: str, *args, **kwargs) -> None:
        """Log a message at the specified level."""
        if not self._logger:
            return

        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }

        log_level = level_map.get(level.lower(), logging.WARNING)
        self._logger.log(log_level, message, *args, **kwargs)

    @property
    def name(self) -> str:
        """Get the logger name."""
        if self._logger:
            return self._logger.name
        return "unknown"

    def get_logger(self) -> logging.Logger | None:
        """Get the underlying logging.Logger instance."""
        return self._logger


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def get_logger(
    name: str | None = None,
    level: LoggerLevel | None = None,
    rich: bool = True,
    color: ColorName | Color | str = None,
    display_all: bool = False,
) -> Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger. If None, defaults to the caller's function name.
        level: Logging level. If None, defaults to "debug" if display_all else "warning"
        rich: Whether to use rich formatting for output
        color: The color for the loggers name.
        display_all: If True, sets effective level to debug to show all messages

    Returns:
        A Logger instance with the specified configuration.
    """
    if name is None:
        name = inspect.currentframe().f_back.f_code.co_name

    return Logger(name, level, rich, display_all)
