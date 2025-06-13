"""hammad._internal

Contains a light initialization group of resources that are
used at a base level throughout the library, as well as serves
as a grounded import location for a couple external imports.
"""

import logging
from logging import getLogger as _get_logger, Filter
from typing import Any, Self

# outbound imports
from rich import get_console as _get_console
from rich.logging import RichHandler as _RichHandler

__all__ = (
    "_get_console",
    "_get_logger",
    "_ConfigKey",
    "_ConfigManager",
    "_get_hammad_lib_config_manager",
    "_get_hammad_lib_config_var",
    "_set_hammad_lib_config_var",
)


class _BaseLoggerStyledFilter(Filter):
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


# logger
_logger = _get_logger("hammad")
"""initializes the logger for the `hammad` library."""
# clear handlers / filters
handler = _RichHandler(
    level=logging.ERROR,
    console=_get_console,
    rich_tracebacks=True,
    show_time=False,
    show_path=False,
    markup=True,
)
formatter = logging.Formatter("| [bold]✼ {name}[/bold] - {message}", style="{")
handler.setFormatter(formatter)
handler.addFilter(_BaseLoggerStyledFilter())
_logger.addHandler(handler)


class _ConfigKey(str):
    """A key for a configuration entry."""

    def __new__(cls, value: str) -> Self:
        if not value.isidentifier():
            raise ValueError(f"Invalid configuration key: {value}")
        return super().__new__(cls, value)


class _ConfigManager:
    """Manages the internal configuration for the `hammad` library."""

    _instance: "Self | None" = None
    _initialized: bool = False

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not _ConfigManager._initialized:
            self._config: dict[str, Any] = {}
            _ConfigManager._initialized = True

    def get_entry(self, key: str) -> Any:
        """Gets an entry from the configuration."""
        config_key = _ConfigKey(key)
        return self._config.get(config_key)

    def set_entry(self, key: str, value: Any) -> None:
        """Sets an entry in the configuration."""
        config_key = _ConfigKey(key)
        self._config[config_key] = value


# ------------------------------------------------------------
# Config Helpers
# ------------------------------------------------------------


def _get_hammad_lib_config_manager() -> _ConfigManager:
    """Gets the `_ConfigManager` instance."""
    return _ConfigManager()


def _get_hammad_lib_config_var(key: str) -> Any:
    """Gets a variable from the `hammad` library configuration."""
    return _get_hammad_lib_config_manager().get_entry(key)


def _set_hammad_lib_config_var(key: str, value: Any) -> None:
    """Sets a variable in the `hammad` library configuration."""
    return _get_hammad_lib_config_manager().set_entry(key, value)
