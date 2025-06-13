"""hammad._internal._settings"""

# settings are managed in a key value store
# this specific instance is not meant to be used
# by users

__all__ = ["_get_internal_settings_manager"]


class _Key(str):
    """A key for a configuration entry into the
    internal settings store."""

    def __new__(cls, value: str) -> "_Key":
        if not value.isidentifier():
            raise ValueError(f"Invalid configuration key: {value}")
        return super().__new__(cls, value)


class _InternalSettingsManager:
    """Internal manager that handles the 'global' library settings
    during execution life-cycle."""

    _manager: "_InternalSettingsManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "_InternalSettingsManager":
        if cls._manager is None:
            cls._manager = super().__new__(cls)
        return cls._manager

    def __init__(self) -> None:
        if not _InternalSettingsManager._initialized:
            self._config: dict[_Key, object] = {}
            _InternalSettingsManager._initialized = True

    def get_entry(self, key: str) -> object:
        """Gets an entry from the configuration."""
        config_key = _Key(key)
        return self._config.get(config_key)

    def set_entry(self, key: str, value: object) -> None:
        """Sets an entry in the configuration."""
        config_key = _Key(key)
        self._config[config_key] = value

    def delete_entry(self, key: str) -> None:
        """Deletes an entry from the configuration."""
        config_key = _Key(key)
        self._config.pop(config_key, None)

    def configure_entries(self, entries: list[str, object]) -> None:
        """Initializes fields for a list of entry names
        in the configuration (Used by modules with multiple
        internal settings)."""
        for entry, value in entries.items():
            self.set_entry(entry, value)


def _get_internal_settings_manager() -> _InternalSettingsManager:
    """Returns the singleton instance of the `_InternalSettingsManager`
    class."""
    return _InternalSettingsManager()
