"""hammad._core

Contains a light initialization group of resources that are
used at a base level throughout the library, as well as serves
as a grounded import location for a couple external imports.

"""

from logging import getLogger as _get_logger
from typing import Any, Self

# outbound imports
from rich import get_console as _get_console

__all__ = (
    "_get_console",
    "_get_logger",
    "_ConfigKey",
    "_ConfigManager",
    "_get_hammad_lib_config_manager",
    "_get_hammad_lib_config_var",
    "_set_hammad_lib_config_var",
)


# logger
_logger = _get_logger("hammad")
"""initializes the logger for the `hammad` library."""


class _ConfigKey(str):
    """A key for a configuration entry."""

    def __new__(cls, value: str) -> Self:
        if not value.isidentifier():
            raise ValueError(f"Invalid configuration key: {value}")
        return super().__new__(cls, value)


class _ConfigManager:
    """Manages the internal configuration for the `hammad` library."""
    
    _instance: 'Self | None' = None
    _initialized: bool = False

    def __new__(cls) -> 'Self':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not _ConfigManager._initialized:
            self._config: dict[str, Any] = {}
            _ConfigManager._initialized = True

    def get_entry(self, key : str) -> Any:
        """Gets an entry from the configuration."""
        config_key = _ConfigKey(key)
        return self._config.get(config_key)
    
    def set_entry(self, key : str, value : Any) -> None:
        """Sets an entry in the configuration."""
        config_key = _ConfigKey(key)
        self._config[config_key] = value


# ------------------------------------------------------------
# Config Helpers
# ------------------------------------------------------------


def _get_hammad_lib_config_manager() -> _ConfigManager:
    """Gets the `_ConfigManager` instance."""
    return _ConfigManager()


def _get_hammad_lib_config_var(key : str) -> Any:
    """Gets a variable from the `hammad` library configuration."""
    return _get_hammad_lib_config_manager().get_entry(key)


def _set_hammad_lib_config_var(key : str, value : Any) -> None:
    """Sets a variable in the `hammad` library configuration."""
    return _get_hammad_lib_config_manager().set_entry(key, value)