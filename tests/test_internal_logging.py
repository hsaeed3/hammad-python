import pytest
from hammad._internal import _logging
import logging
from unittest.mock import patch, MagicMock
from hammad._internal._settings import _get_internal_settings_manager


class TestBaseLoggerStyledFilter:
    """Tests for the _BaseLoggerStyledFilter class."""
    
    def test_filter_critical_level(self):
        """Test that CRITICAL level messages get bold red styling."""
        filter_instance = _logging._BaseLoggerStyledFilter()
        record = logging.LogRecord(
            name="test", level=logging.CRITICAL, pathname="", lineno=0, 
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.msg == "[bold red]test message[/bold red]"
    
    def test_filter_error_level(self):
        """Test that ERROR level messages get italic red styling."""
        filter_instance = _logging._BaseLoggerStyledFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.msg == "[italic red]test message[/italic red]"
    
    def test_filter_warning_level(self):
        """Test that WARNING level messages get italic yellow styling."""
        filter_instance = _logging._BaseLoggerStyledFilter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.msg == "[italic yellow]test message[/italic yellow]"
    
    def test_filter_info_level(self):
        """Test that INFO level messages get white styling."""
        filter_instance = _logging._BaseLoggerStyledFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.msg == "[white]test message[/white]"
    
    def test_filter_debug_level(self):
        """Test that DEBUG level messages get italic dim white styling."""
        filter_instance = _logging._BaseLoggerStyledFilter()
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.msg == "[italic dim white]test message[/italic dim white]"


class TestConfigureLoggingInternalSettings:
    """Tests for the _configure_logging_internal_settings function."""
    
    def test_configure_logging_internal_settings(self):
        """Test that internal settings are properly configured."""
        # Reset settings manager state
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
        
        _logging._configure_logging_internal_settings()
        
        assert settings_manager.get_entry("LOGGING_LEVEL") == logging.ERROR
        assert settings_manager.get_entry("LOGGING_CURRENT_LOGGER_LEVEL") is None
        assert settings_manager.get_entry("LOGGING_RICH_ENABLED") is True


class TestSetHammadLoggerLevel:
    """Tests for the _set_hammad_logger_level function."""
    
    def setup_method(self):
        """Reset logger state before each test."""
        _logging._hammad_logger = None
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
        _logging._configure_logging_internal_settings()
    
    def test_set_logger_level_with_string_debug(self):
        """Test setting logger level with string 'DEBUG'."""
        _logging._set_hammad_logger_level("DEBUG")
        
        settings_manager = _get_internal_settings_manager()
        assert settings_manager.get_entry("LOGGING_CURRENT_LOGGER_LEVEL") == "DEBUG"
    
    def test_set_logger_level_with_string_lowercase(self):
        """Test setting logger level with lowercase string."""
        _logging._set_hammad_logger_level("info")
        
        settings_manager = _get_internal_settings_manager()
        assert settings_manager.get_entry("LOGGING_CURRENT_LOGGER_LEVEL") == "INFO"
    
    def test_set_logger_level_with_int(self):
        """Test setting logger level with integer value."""
        _logging._set_hammad_logger_level(logging.WARNING)
        
        settings_manager = _get_internal_settings_manager()
        assert settings_manager.get_entry("LOGGING_CURRENT_LOGGER_LEVEL") == logging.WARNING
    
    def test_set_logger_level_invalid_string(self):
        """Test that invalid string level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid logging level: INVALID"):
            _logging._set_hammad_logger_level("INVALID")
    
    def test_set_logger_level_updates_existing_logger(self):
        """Test that existing logger level is updated."""
        # Create logger first
        logger = _logging._get_hammad_logger()
        initial_level = logger.level
        
        _logging._set_hammad_logger_level("DEBUG")
        
        # Logger level should be updated
        assert logger.level != initial_level


class TestGetHammadCurrentLoggerLevel:
    """Tests for the _get_hammad_current_logger_level function."""
    
    def setup_method(self):
        """Reset settings before each test."""
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
        _logging._configure_logging_internal_settings()
    
    def test_get_current_logger_level_default(self):
        """Test getting current logger level returns default when not set."""
        result = _logging._get_hammad_current_logger_level()
        assert result == logging.ERROR
    
    def test_get_current_logger_level_after_setting(self):
        """Test getting current logger level after setting it."""
        _logging._set_hammad_logger_level("DEBUG")
        result = _logging._get_hammad_current_logger_level()
        assert result == "DEBUG"


class TestGetHammadLogger:
    """Tests for the _get_hammad_logger function."""
    
    def setup_method(self):
        """Reset logger state before each test."""
        _logging._hammad_logger = None
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
        _logging._configure_logging_internal_settings()
    
    def test_get_logger_creates_new_logger(self):
        """Test that a new logger is created when none exists."""
        logger = _logging._get_hammad_logger()
        
        assert logger is not None
        assert logger.name == "hammad"
        assert _logging._hammad_logger is logger
    
    def test_get_logger_returns_existing_logger(self):
        """Test that the same logger instance is returned on subsequent calls."""
        logger1 = _logging._get_hammad_logger()
        logger2 = _logging._get_hammad_logger()
        
        assert logger1 is logger2
    
    @patch('hammad._internal._logging._update_logger_configuration')
    def test_get_logger_updates_configuration_when_changed(self, mock_update):
        """Test that logger configuration is updated when settings change."""
        # Create logger first
        logger = _logging._get_hammad_logger()
        mock_update.reset_mock()
        
        # Change settings
        settings_manager = _get_internal_settings_manager()
        settings_manager.set_entry("LOGGING_LEVEL", logging.DEBUG)
        
        # Get logger again
        _logging._get_hammad_logger()
        
        # Configuration should be updated
        mock_update.assert_called_once()


class TestUpdateLoggerConfiguration:
    """Tests for the _update_logger_configuration function."""
    
    def setup_method(self):
        """Reset logger state before each test."""
        _logging._hammad_logger = None
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
        _logging._configure_logging_internal_settings()
    
    def test_update_configuration_with_no_logger(self):
        """Test that update does nothing when no logger exists."""
        # Should not raise an exception
        _logging._update_logger_configuration()
    
    @patch('hammad._internal._logging.RichHandler')
    @patch('hammad._internal._logging.get_console')
    def test_update_configuration_with_rich_enabled(self, mock_console, mock_rich_handler):
        """Test logger configuration with Rich enabled."""
        # Create logger
        _logging._hammad_logger = logging.getLogger("hammad")
        
        # Configure with Rich enabled
        settings_manager = _get_internal_settings_manager()
        settings_manager.set_entry("LOGGING_RICH_ENABLED", True)
        settings_manager.set_entry("LOGGING_LEVEL", logging.INFO)
        
        _logging._update_logger_configuration()
        
        # RichHandler should be created
        mock_rich_handler.assert_called_once()
        assert _logging._hammad_logger.level == logging.INFO
    
    def test_update_configuration_with_rich_disabled(self):
        """Test logger configuration with Rich disabled."""
        # Create logger
        _logging._hammad_logger = logging.getLogger("hammad")
        
        # Configure with Rich disabled
        settings_manager = _get_internal_settings_manager()
        settings_manager.set_entry("LOGGING_RICH_ENABLED", False)
        settings_manager.set_entry("LOGGING_LEVEL", logging.WARNING)
        
        _logging._update_logger_configuration()
        
        # StreamHandler should be used
        assert len(_logging._hammad_logger.handlers) == 1
        assert isinstance(_logging._hammad_logger.handlers[0], logging.StreamHandler)
        assert _logging._hammad_logger.level == logging.WARNING
    
    def test_update_configuration_clears_existing_handlers(self):
        """Test that existing handlers are cleared before adding new ones."""
        # Create logger with existing handler
        _logging._hammad_logger = logging.getLogger("hammad")
        existing_handler = logging.StreamHandler()
        _logging._hammad_logger.addHandler(existing_handler)
        
        # Update configuration
        _logging._update_logger_configuration()
        
        # Old handler should be removed
        assert existing_handler not in _logging._hammad_logger.handlers
        assert len(_logging._hammad_logger.handlers) == 1


class TestLoggerLevelsDict:
    """Tests for the _logger_levels dictionary."""
    
    def test_logger_levels_structure(self):
        """Test that _logger_levels contains expected entries."""
        assert "DEBUG" in _logging._logger_levels
        assert "INFO" in _logging._logger_levels
        assert "WARNING" in _logging._logger_levels
        assert "ERROR" in _logging._logger_levels
        assert "CRITICAL" in _logging._logger_levels
    
    def test_debug_level_contains_variants(self):
        """Test that DEBUG level contains all expected variants."""
        debug_values = _logging._logger_levels["DEBUG"]
        assert logging.DEBUG in debug_values
        assert "DEBUG" in debug_values
        assert "debug" in debug_values
    
    def test_info_level_contains_variants(self):
        """Test that INFO level contains all expected variants."""
        info_values = _logging._logger_levels["INFO"]
        assert logging.INFO in info_values
        assert "INFO" in info_values
        assert "info" in info_values


class TestIntegration:
    """Integration tests for the logging module."""
    
    def setup_method(self):
        """Reset state before each test."""
        _logging._hammad_logger = None
        settings_manager = _get_internal_settings_manager()
        settings_manager._config.clear()
    
    def test_full_logging_workflow(self):
        """Test the complete logging workflow."""
        # Configure settings
        _logging._configure_logging_internal_settings()
        
        # Set a custom level
        _logging._set_hammad_logger_level("INFO")
        
        # Get logger
        logger = _logging._get_hammad_logger()
        
        # Verify logger is properly configured
        assert logger.name == "hammad"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
        
        # Verify settings are updated
        current_level = _logging._get_hammad_current_logger_level()
        assert current_level == "INFO"
    
    def test_logger_reconfiguration(self):
        """Test that logger can be reconfigured dynamically."""
        # Initial setup
        _logging._configure_logging_internal_settings()
        logger = _logging._get_hammad_logger()
        initial_handler_count = len(logger.handlers)
        
        # Change Rich setting
        settings_manager = _get_internal_settings_manager()
        settings_manager.set_entry("LOGGING_RICH_ENABLED", False)
        settings_manager.set_entry("LOGGING_LEVEL", logging.DEBUG)
        
        # Get logger again (should trigger reconfiguration)
        logger = _logging._get_hammad_logger()
        
        # Verify reconfiguration
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1  # Should still have one handler
