"""hammad._internal._logging

Contains internal logging resources and utilities meant
for private use within the library."""

import logging
from rich import get_console
from rich.logging import RichHandler

from ._settings import _get_internal_settings_manager


_hammad_logger : logging.Logger | None = None
"""The logger instance for the `hammad` library."""


_logger_levels = {
    "DEBUG": [logging.DEBUG, "DEBUG", "debug"],
    "INFO": [logging.INFO, "INFO", "info"],
    "WARNING": [logging.WARNING, "WARNING", "warning"],
    "ERROR": [logging.ERROR, "ERROR", "error"],
    "CRITICAL": [logging.CRITICAL, "CRITICAL", "critical"],
}


class _BaseLoggerStyledFilter(logging.Filter):
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


def _configure_logging_internal_settings() -> None:
    """Configures the variables used within the internal
    `_logging` module, shared across the package."""

    internal_settings_manager = _get_internal_settings_manager()
    internal_settings_manager.configure_entries(
        {
            # User Defined
            "LOGGING_LEVEL": logging.ERROR,
            # Used to update the current logger level
            "LOGGING_CURRENT_LOGGER_LEVEL": None,
            "LOGGING_RICH_ENABLED": True,
        }
    )


def _set_hammad_logger_level(level: str | int) -> None:
    """Sets the logging level for the hammad logger."""
    global _hammad_logger
    if isinstance(level, str):
        original_level = level.upper()
        level = level.upper()
        for key, value in _logger_levels.items():
            if level in value:
                level = value[0]  # Use the integer value from the logger_levels dict
                break
        else:
            raise ValueError(f"Invalid logging level: {level}")
        settings_level = original_level
    else:
        # For integer input, store the integer
        settings_level = level
    
    if _hammad_logger is not None:
        _hammad_logger.setLevel(level)
    _get_internal_settings_manager().set_entry("LOGGING_CURRENT_LOGGER_LEVEL", settings_level)


def _get_hammad_current_logger_level() -> str | int:
    """Gets the current logging level for the hammad logger."""
    return _get_internal_settings_manager().get_entry("LOGGING_CURRENT_LOGGER_LEVEL") or logging.ERROR


def _get_hammad_logger() -> logging.Logger:
    """Returns the logger instance for the `hammad` library."""
    global _hammad_logger

    if _hammad_logger is None:
        _hammad_logger = logging.getLogger("hammad")
        _update_hammad_logger_configuration()
    else:
        # Check if configuration has changed
        current_level = _get_internal_settings_manager().get_entry("LOGGING_LEVEL")
        current_rich_enabled = _get_internal_settings_manager().get_entry("LOGGING_RICH_ENABLED")
        if _hammad_logger.level != current_level or len(_hammad_logger.handlers) == 0 or (_hammad_logger.handlers[0].__class__.__name__ == 'RichHandler') != current_rich_enabled:
            _update_hammad_logger_configuration()

    return _hammad_logger


def _update_hammad_logger_configuration() -> None:
    """Updates the logger configuration based on current settings."""
    global _hammad_logger
    if _hammad_logger is None:
        return

    # Clear existing handlers
    _hammad_logger.handlers.clear()

    # Set the logging level - use current logger level if set, otherwise use default
    current_logger_level = _get_internal_settings_manager().get_entry("LOGGING_CURRENT_LOGGER_LEVEL")
    if current_logger_level is not None:
        # If a level was explicitly set, use it
        if isinstance(current_logger_level, str):
            # Convert string level to integer
            for key, value in _logger_levels.items():
                if current_logger_level in value:
                    current_level = value[0]
                    break
            else:
                current_level = _get_internal_settings_manager().get_entry("LOGGING_LEVEL")
        else:
            current_level = current_logger_level
    else:
        current_level = _get_internal_settings_manager().get_entry("LOGGING_LEVEL")
    
    _hammad_logger.setLevel(current_level)

    if _get_internal_settings_manager().get_entry("LOGGING_RICH_ENABLED"):
        handler = RichHandler(
            level=current_level,
            console=get_console(),
            rich_tracebacks=True,
            show_time=False,
            show_path=False,
            markup=True,
        )
        formatter = logging.Formatter("| [bold]✼ {name}[/bold] - {message}", style="{")
        handler.setFormatter(formatter)
        handler.addFilter(_BaseLoggerStyledFilter())
        _hammad_logger.addHandler(handler)
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("| ✼ {name} - {message}", style="{")
        handler.setFormatter(formatter)
        _hammad_logger.addHandler(handler)