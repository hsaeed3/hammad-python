"""hammad._internal._settings"""

# settings are managed in a key value store
# this specific instance is not meant to be used
# by users

__all__ = ["_get_hammad_settings_manager"]


class _Key(str):
    """A key for a configuration entry into the
    internal settings store."""

    def __new__(cls, value: str) -> "_Key":
        if not value.isidentifier():
            raise ValueError(f"Invalid configuration key: {value}")
        return super().__new__(cls, value)


class _HammadSettingsManager:
    """Internal manager that handles the 'global' library settings
    during execution life-cycle."""

    _manager: "_HammadSettingsManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "_HammadSettingsManager":
        if cls._manager is None:
            cls._manager = super().__new__(cls)
        return cls._manager

    def __init__(self) -> None:
        if not _HammadSettingsManager._initialized:
            self._config: dict[_Key, object] = {}
            _HammadSettingsManager._initialized = True

    def get_entry(self, key: str) -> object:
        """Gets an entry from the configuration."""
        config_key = _Key(key)
        return self._config.get(config_key)

    def set_entry(self, key: str, value: object) -> None:
        """Sets an entry in the configuration."""
        config_key = _Key(key)
        self._config[config_key] = value


def _get_hammad_settings_manager() -> _HammadSettingsManager:
    """Returns the singleton instance of the `_HammadSettingsManager`
    class."""
    global _HAMMAD_SETTINGS_MANAGER

    if not _HAMMAD_SETTINGS_MANAGER:
        _HAMMAD_SETTINGS_MANAGER = _HammadSettingsManager()
    return _HAMMAD_SETTINGS_MANAGER
