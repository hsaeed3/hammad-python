import pytest
import logging
from hammad.logging import logger as logger_module


def test_logger_creation_with_defaults():
    """Test creating a logger with default settings."""
    logger = logger_module.get_logger()
    
    assert logger.name is not None
    assert logger.level == "info"  # Default when display_all=False
    assert isinstance(logger.get_logger(), logging.Logger)


def test_logger_creation_with_custom_name():
    """Test creating a logger with a custom name."""
    logger = logger_module.get_logger(name="test_logger")
    
    assert logger.name == "test_logger"


def test_logger_creation_with_display_all():
    """Test creating a logger with display_all=True."""
    logger = logger_module.get_logger(display_all=True)
    
    assert logger.level == "debug"  # Should default to debug when display_all=True


def test_logger_level_setting():
    """Test setting logger levels."""
    logger = logger_module.get_logger()
    
    # Test setting standard levels
    logger.level = "debug"
    assert logger.level == "debug"
    
    logger.level = "warning"
    assert logger.level == "warning"
    
    logger.level = "error"
    assert logger.level == "error"


def test_logger_standard_logging_methods():
    """Test standard logging methods work without errors."""
    logger = logger_module.get_logger(name="test_methods")
    
    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_logger_log_method():
    """Test the generic log method."""
    logger = logger_module.get_logger(name="test_log")
    
    # Test with string levels
    logger.log("debug", "Debug via log method")
    logger.log("info", "Info via log method")
    
    # Test with numeric levels
    logger.log(logging.DEBUG, "Debug via numeric level")
    logger.log(logging.INFO, "Info via numeric level")


def test_logger_is_enabled_for():
    """Test the is_enabled_for method."""
    logger = logger_module.get_logger(level="warning")
    
    assert not logger.is_enabled_for("debug")
    assert not logger.is_enabled_for("info")
    assert logger.is_enabled_for("warning")
    assert logger.is_enabled_for("error")
    assert logger.is_enabled_for("critical")
    
    # Test with numeric levels
    assert not logger.is_enabled_for(logging.DEBUG)
    assert logger.is_enabled_for(logging.WARNING)


def test_logger_handlers():
    """Test logger handler management."""
    logger = logger_module.get_logger(name="test_handlers")
    
    # Should have at least one handler (RichHandler)
    assert len(logger.handlers) > 0
    
    # Test adding a handler
    handler = logging.StreamHandler()
    logger.add_handler(handler)
    assert handler in logger.handlers
    
    # Test removing a handler
    logger.remove_handler(handler)
    assert handler not in logger.handlers


def test_logger_set_level_method():
    """Test the set_level method."""
    logger = logger_module.get_logger()
    
    # Test with string
    logger.set_level("error")
    assert logger.level == "error"
    
    # Test with numeric level
    logger.set_level(logging.DEBUG)
    assert logger.level == "debug"


def test_logger_add_custom_level():
    """Test adding custom logging levels."""
    logger = logger_module.get_logger(name="test_custom")
    
    # Add a custom level
    logger.add_level("trace", value=5)
    
    # Should be able to log at custom level
    logger.log("trace", "This is a trace message")
    
    # Should be able to check if enabled
    logger.set_level("trace")
    assert logger.is_enabled_for("trace")


def test_logger_update_level_style():
    """Test updating level styles."""
    logger = logger_module.get_logger(name="test_style")
    
    # This should not raise an exception
    style_config = {
        "show_name": True,
        "show_level": True,
        "level_style": "bold red",
        "message_style": "red"
    }
    logger.update_level_style("error", style_config)


def test_logger_update_settings():
    """Test updating logger settings."""
    logger = logger_module.get_logger(name="test_settings")
    
    # This should not raise an exception
    new_settings = {
        "show_time": True,
        "show_path": True,
        "prefix": "TEST"
    }
    logger.update_settings(new_settings)


def test_logger_exception_method():
    """Test the exception logging method."""
    logger = logger_module.get_logger(name="test_exception")
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        # This should not raise an exception
        logger.exception("An error occurred")


def test_logger_with_custom_levels_in_init():
    """Test creating logger with custom levels in initialization."""
    custom_levels = {
        "trace": {
            "show_name": True,
            "show_level": True,
            "level_style": "dim white",
            "message_style": "dim white"
        }
    }
    
    logger = logger_module.get_logger(
        name="test_custom_init",
        levels=custom_levels
    )
    
    # Should be able to use the custom level
    logger.log("trace", "Trace message")


def test_logger_with_rich_styling():
    """Test logger creation with rich styling options."""
    logger = logger_module.get_logger(
        name="test_rich",
        style="bold blue",
        prefix="TEST",
        show_time=True,
        show_path=False,
        show_level=True,
        show_name=True
    )
    
    # Should create without errors
    assert logger.name == "test_rich"
    logger.info("Styled message")


def test_logger_class_direct_instantiation():
    """Test direct instantiation of Logger class."""
    logger = logger_module.Logger(
        name="direct_test",
        level="warning",
        display_all=False
    )
    
    assert logger.name == "direct_test"
    assert logger.level == "warning"
    logger.warning("Direct instantiation test")


def test_logger_get_logger_property():
    """Test getting the underlying logging.Logger instance."""
    logger = logger_module.get_logger(name="test_underlying")
    underlying = logger.get_logger()
    
    assert isinstance(underlying, logging.Logger)
    assert underlying.name == "test_underlying"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])