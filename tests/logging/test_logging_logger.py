import pytest
from hammad.logging import logger


class TestLogger:
    """Test cases for the Logger class."""

    def test_logger_creation_with_defaults(self):
        """Test creating a logger with default settings."""
        log = logger.create_logger()
        assert (
            log.name == "test_logger_creation_with_defaults"
        )  # Should use function name
        assert log.level == "warning"  # Default level
        assert len(log.handlers) == 1

    def test_logger_creation_with_custom_name(self):
        """Test creating a logger with a custom name."""
        log = logger.create_logger(name="test_logger")
        assert log.name == "test_logger"

    def test_logger_creation_with_custom_level(self):
        """Test creating a logger with a custom level."""
        log = logger.create_logger(level="debug")
        assert log.level == "debug"

    def test_logger_creation_with_display_all(self):
        """Test creating a logger with display_all=True."""
        log = logger.create_logger(display_all=True)
        # When display_all is True, effective level should be debug regardless of user level
        assert log._logger.level == 10  # DEBUG level

    def test_logger_creation_with_rich_disabled(self):
        """Test creating a logger with rich formatting disabled."""
        log = logger.create_logger(rich=False)
        # Should have a StreamHandler instead of RichHandler
        assert len(log.handlers) == 1
        handler = log.handlers[0]
        assert type(handler).__name__ == "StreamHandler"

    def test_logger_level_property_getter(self):
        """Test getting the logger level."""
        log = logger.create_logger(level="info")
        assert log.level == "info"

    def test_logger_level_property_setter(self):
        """Test setting the logger level."""
        log = logger.create_logger(level="info")
        log.level = "error"
        assert log.level == "error"

    def test_logger_standard_logging_methods(self):
        """Test the standard logging methods (debug, info, warning, error, critical)."""
        log = logger.create_logger(level="debug")

        # These should not raise exceptions
        log.debug("Debug message")
        log.info("Info message")
        log.warning("Warning message")
        log.error("Error message")
        log.critical("Critical message")

    def test_logger_generic_log_method(self):
        """Test the generic log method with different levels."""
        log = logger.create_logger(level="debug")

        # These should not raise exceptions
        log.log("debug", "Debug message")
        log.log("info", "Info message")
        log.log("warning", "Warning message")
        log.log("error", "Error message")
        log.log("critical", "Critical message")

    def test_logger_add_custom_level(self):
        """Test adding a custom logging level."""
        log = logger.create_logger(level="debug")

        # Add a custom level
        log.add_level("trace", 5)

        # Should be able to log at this level
        log.log("trace", "Trace message")

        # Custom level should be stored
        assert "trace" in log._custom_levels
        assert log._custom_levels["trace"] == 5

    def test_logger_add_custom_level_with_style(self):
        """Test adding a custom logging level with style settings."""
        log = logger.create_logger(level="debug")

        style_config = {"message": "green bold", "title": "green"}

        log.add_level("success", 25, style=style_config)

        # Should be able to log at this level
        log.log("success", "Success message")

        # Style should be stored
        assert "success" in log._level_styles
        assert log._level_styles["success"] == style_config

    def test_logger_custom_level_styles_on_creation(self):
        """Test creating a logger with custom level styles."""
        custom_styles = {"debug": {"message": "cyan", "title": "cyan bold"}}

        log = logger.create_logger(level="debug", levels=custom_styles)

        # Custom style should override default
        assert log._level_styles["debug"]["message"] == "cyan"
        assert log._level_styles["debug"]["title"] == "cyan bold"

    def test_logger_get_underlying_logger(self):
        """Test getting the underlying logging.Logger instance."""
        log = logger.create_logger()
        underlying = log.get_logger()

        import logging

        assert isinstance(underlying, logging.Logger)
        assert underlying.name == log.name


class TestLoggerLevelCreation:
    """Test cases for create_logger_level function."""

    def test_create_logger_level_basic(self):
        """Test creating a basic custom logging level."""
        import logging

        # Create a custom level
        logger.create_logger_level("TRACE", 5)

        # Should be added to logging module
        assert logging.getLevelName(5) == "TRACE"

    def test_create_logger_level_with_color_and_style(self):
        """Test creating a custom logging level with color and style."""
        import logging

        # Create a custom level with styling
        logger.create_logger_level("SUCCESS", 25, color="green", style="bold")

        # Should be added to logging module
        assert logging.getLevelName(25) == "SUCCESS"

        # Should have custom level info stored
        assert hasattr(logging, "_custom_level_info")
        assert 25 in logging._custom_level_info
        assert logging._custom_level_info[25]["name"] == "SUCCESS"
        assert logging._custom_level_info[25]["color"] == "green"
        assert logging._custom_level_info[25]["style"] == "bold"


class TestDefaultLevelStyles:
    """Test cases for default level styles."""

    def test_default_level_styles_exist(self):
        """Test that default level styles are properly defined."""
        from hammad.logging.logger import DEFAULT_LEVEL_STYLES

        expected_levels = ["critical", "error", "warning", "info", "debug"]

        for level in expected_levels:
            assert level in DEFAULT_LEVEL_STYLES
            assert "message" in DEFAULT_LEVEL_STYLES[level]


class TestRichLoggerFilter:
    """Test cases for RichLoggerFilter."""

    def test_rich_logger_filter_creation(self):
        """Test creating a RichLoggerFilter."""
        from hammad.logging.logger import RichLoggerFilter

        level_styles = {"debug": {"message": "white"}}
        filter_obj = RichLoggerFilter(level_styles)

        assert filter_obj.level_styles == level_styles

    def test_rich_logger_filter_adds_style_config(self):
        """Test that RichLoggerFilter adds style config to log records."""
        import logging
        from hammad.logging.logger import RichLoggerFilter

        level_styles = {"debug": {"message": "white bold"}}
        filter_obj = RichLoggerFilter(level_styles)

        # Create a mock log record
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Filter should add style config
        result = filter_obj.filter(record)
        assert result is True
        assert hasattr(record, "_hammad_style_config")
        assert record._hammad_style_config == level_styles["debug"]


class TestRichLoggerFormatter:
    """Test cases for RichLoggerFormatter."""

    def test_rich_logger_formatter_creation(self):
        """Test creating a RichLoggerFormatter."""
        from hammad.logging.logger import RichLoggerFormatter

        formatter = RichLoggerFormatter()
        assert formatter is not None
        assert hasattr(formatter, "console")

    def test_rich_logger_formatter_build_style_string(self):
        """Test building style strings from style dictionaries."""
        from hammad.logging.logger import RichLoggerFormatter

        formatter = RichLoggerFormatter()

        # Test with bold and italic
        style_dict = {"bold": True, "italic": True}
        result = formatter._build_renderable_style_string(style_dict)
        assert "bold" in result
        assert "italic" in result

        # Test with no styles
        style_dict = {}
        result = formatter._build_renderable_style_string(style_dict)
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
