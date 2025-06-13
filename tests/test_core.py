import pytest
from hammad._internal import (
    _get_console,
    _get_logger,
    _ConfigKey,
    _ConfigManager,
    _get_hammad_lib_config_manager,
    _get_hammad_lib_config_var,
    _set_hammad_lib_config_var,
)


def test_get_console():
    """Test that _get_console returns a console object."""
    console = _get_console()
    assert console is not None
    # Should return the same instance each time
    assert _get_console() is console


def test_get_logger():
    """Test that _get_logger returns a logger object."""
    logger = _get_logger("test")
    assert logger is not None
    assert logger.name == "test"


def test_config_key_valid():
    """Test that _ConfigKey accepts valid identifiers."""
    key = _ConfigKey("valid_key")
    assert key == "valid_key"
    assert isinstance(key, str)


def test_config_key_invalid():
    """Test that _ConfigKey raises ValueError for invalid identifiers."""
    with pytest.raises(ValueError, match="Invalid configuration key"):
        _ConfigKey("invalid-key")

    with pytest.raises(ValueError, match="Invalid configuration key"):
        _ConfigKey("123invalid")

    with pytest.raises(ValueError, match="Invalid configuration key"):
        _ConfigKey("invalid key")


def test_config_manager_singleton():
    """Test that _ConfigManager is a singleton."""
    manager1 = _ConfigManager()
    manager2 = _ConfigManager()
    assert manager1 is manager2


def test_config_manager_get_set():
    """Test getting and setting configuration entries."""
    manager = _ConfigManager()

    # Test setting and getting a value
    manager.set_entry("test_key", "test_value")
    assert manager.get_entry("test_key") == "test_value"

    # Test getting non-existent key returns None
    assert manager.get_entry("nonexistent") is None


def test_config_manager_invalid_key():
    """Test that _ConfigManager raises ValueError for invalid keys."""
    manager = _ConfigManager()

    with pytest.raises(ValueError, match="Invalid configuration key"):
        manager.set_entry("invalid-key", "value")

    with pytest.raises(ValueError, match="Invalid configuration key"):
        manager.get_entry("invalid-key")


def test_hammad_lib_config_functions():
    """Test the helper functions for hammad library configuration."""
    # Test getting the config manager
    manager = _get_hammad_lib_config_manager()
    assert isinstance(manager, _ConfigManager)

    # Test setting and getting a config variable
    _set_hammad_lib_config_var("test_setting", "test_value")
    assert _get_hammad_lib_config_var("test_setting") == "test_value"

    # Test getting non-existent variable returns None
    assert _get_hammad_lib_config_var("nonexistent_setting") is None


def test_config_manager_initialization():
    """Test that _ConfigManager initializes properly."""
    manager = _ConfigManager()
    assert manager._config is not None
    assert isinstance(manager._config, dict)
    assert manager._initialized is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
