import pytest
from hammad._internal import _settings
from unittest.mock import patch, MagicMock


class TestKey:
    """Tests for the _Key class."""
    
    def test_valid_key_creation(self):
        """Test that valid identifiers can be used as keys."""
        key = _settings._Key("valid_key")
        assert key == "valid_key"
        assert isinstance(key, _settings._Key)
    
    def test_invalid_key_creation(self):
        """Test that invalid identifiers raise ValueError."""
        with pytest.raises(ValueError, match="Invalid configuration key: 123invalid"):
            _settings._Key("123invalid")
        
        with pytest.raises(ValueError, match="Invalid configuration key: key-with-dash"):
            _settings._Key("key-with-dash")
        
        with pytest.raises(ValueError, match="Invalid configuration key: key with space"):
            _settings._Key("key with space")


class TestInternalSettingsManager:
    """Tests for the _InternalSettingsManager class."""
    
    def setup_method(self):
        """Reset singleton state before each test."""
        _settings._InternalSettingsManager._manager = None
        _settings._InternalSettingsManager._initialized = False
    
    def test_singleton_behavior(self):
        """Test that _InternalSettingsManager is a singleton."""
        manager1 = _settings._InternalSettingsManager()
        manager2 = _settings._InternalSettingsManager()
        assert manager1 is manager2
    
    def test_initialization_only_once(self):
        """Test that initialization only happens once."""
        manager1 = _settings._InternalSettingsManager()
        original_config = manager1._config
        
        manager2 = _settings._InternalSettingsManager()
        assert manager2._config is original_config
    
    def test_get_entry_existing_key(self):
        """Test getting an existing entry."""
        manager = _settings._InternalSettingsManager()
        manager._config[_settings._Key("test_key")] = "test_value"
        
        result = manager.get_entry("test_key")
        assert result == "test_value"
    
    def test_get_entry_nonexistent_key(self):
        """Test getting a nonexistent entry returns None."""
        manager = _settings._InternalSettingsManager()
        result = manager.get_entry("nonexistent_key")
        assert result is None
    
    def test_set_entry(self):
        """Test setting an entry."""
        manager = _settings._InternalSettingsManager()
        manager.set_entry("new_key", "new_value")
        
        assert manager._config[_settings._Key("new_key")] == "new_value"
    
    def test_set_entry_overwrites_existing(self):
        """Test that setting an entry overwrites existing value."""
        manager = _settings._InternalSettingsManager()
        manager.set_entry("key", "old_value")
        manager.set_entry("key", "new_value")
        
        assert manager.get_entry("key") == "new_value"
    
    def test_delete_entry_existing_key(self):
        """Test deleting an existing entry."""
        manager = _settings._InternalSettingsManager()
        manager.set_entry("key_to_delete", "value")
        
        manager.delete_entry("key_to_delete")
        assert manager.get_entry("key_to_delete") is None
    
    def test_delete_entry_nonexistent_key(self):
        """Test deleting a nonexistent entry doesn't raise error."""
        manager = _settings._InternalSettingsManager()
        # Should not raise an exception
        manager.delete_entry("nonexistent_key")
    
    def test_configure_entries(self):
        """Test configuring multiple entries at once."""
        manager = _settings._InternalSettingsManager()
        entries = {
            "key1": "value1",
            "key2": 42,
            "key3": True
        }
        
        manager.configure_entries(entries)
        
        assert manager.get_entry("key1") == "value1"
        assert manager.get_entry("key2") == 42
        assert manager.get_entry("key3") is True
    
    def test_configure_entries_with_invalid_key(self):
        """Test that configure_entries fails with invalid keys."""
        manager = _settings._InternalSettingsManager()
        entries = {"invalid-key": "value"}
        
        with pytest.raises(ValueError, match="Invalid configuration key: invalid-key"):
            manager.configure_entries(entries)


class TestGetInternalSettingsManager:
    """Tests for the _get_internal_settings_manager function."""
    
    def setup_method(self):
        """Reset singleton state before each test."""
        _settings._InternalSettingsManager._manager = None
        _settings._InternalSettingsManager._initialized = False
    
    def test_returns_singleton_instance(self):
        """Test that function returns the singleton instance."""
        manager1 = _settings._get_internal_settings_manager()
        manager2 = _settings._get_internal_settings_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, _settings._InternalSettingsManager)
    
    def test_returns_initialized_manager(self):
        """Test that returned manager is properly initialized."""
        manager = _settings._get_internal_settings_manager()
        
        assert hasattr(manager, '_config')
        assert isinstance(manager._config, dict)
