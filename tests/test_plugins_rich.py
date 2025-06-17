import pytest
import logging
from hammad.plugins.rich import _types, _utils
from rich import print as rich_print


def test_rich_color_tuple_type():
    """Test RichColorTuple type alias."""
    # This is a type alias, so we can't directly test it
    # but we can verify it works with type checking
    color: _types.RichColorTuple = (255, 128, 0)
    assert color == (255, 128, 0)


def test_rich_color_hex_type():
    """Test RichColorHex type alias."""
    color: _types.RichColorHex = "#ff8000"
    assert color == "#ff8000"


def test_rich_style_settings():
    """Test RichStyleSettings TypedDict."""
    style: _types.RichStyleSettings = {"color": "red", "bold": True, "italic": False}
    assert style["color"] == "red"
    assert style["bold"] is True
    assert style["italic"] is False


def test_rich_background_settings():
    """Test RichBackgroundSettings TypedDict."""
    bg: _types.RichBackgroundSettings = {
        "color": "blue",
        "box": "rounded",
        "title": "Test Title",
        "padding": 1,
    }
    assert bg["color"] == "blue"
    assert bg["box"] == "rounded"
    assert bg["title"] == "Test Title"
    assert bg["padding"] == 1


def test_rich_logging_level_settings():
    """Test RichLoggingLevelSettings TypedDict."""
    level_settings: _types.RichLoggingLevelSettings = {
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "level_style": "bold red",
        "message_style": "italic red",
        "background": {"color": "yellow", "box": "rounded"},
    }
    assert level_settings["show_name"] is True
    assert level_settings["level_style"] == "bold red"
    assert level_settings["background"]["color"] == "yellow"


def test_rich_logging_settings():
    """Test RichLoggingSettings TypedDict."""
    logging_settings: _types.RichLoggingSettings = {
        "name": "test_logger",
        "prefix": "TEST",
        "show_name": True,
        "show_level": True,
        "show_time": False,
        "levels": {
            "debug": {"level_style": "dim white", "message_style": "dim italic white"},
            "error": {"level_style": "bold red", "message_style": "red"},
        },
    }
    assert logging_settings["name"] == "test_logger"
    assert logging_settings["prefix"] == "TEST"
    assert "debug" in logging_settings["levels"]


def test_default_logging_level_settings():
    """Test default logging level settings."""
    defaults = _types.RichDefaultLoggingLevelSettings
    
    # Check that all expected levels are present
    expected_levels = ["debug", "info", "warning", "error", "critical"]
    for level in expected_levels:
        assert level in defaults
        assert "show_name" in defaults[level]
        assert "show_level" in defaults[level]


def test_wrap_renderable_with_string_style():
    """Test wrapping a renderable with string style."""
    result = _utils.wrap_renderable_with_rich_config("Hello World", "red")

    rich_print(result)

    # Should return styled text
    assert isinstance(result, _types.RichText)


def test_wrap_renderable_with_tuple_color():
    """Test wrapping a renderable with tuple color."""
    result = _utils.wrap_renderable_with_rich_config(
        "Hello World",
        (255, 0, 0),  # Red RGB
    )

    rich_print(result)

    assert isinstance(result, _types.RichText)


def test_wrap_renderable_with_dict_style():
    """Test wrapping a renderable with dictionary style."""
    style_dict: _types.RichRenderableSettings = {
        "color": "green",
        "bold": True,
        "italic": True,
        "background": {
            "color": "yellow",
            "box": "double",
            "title": "Test Panel",
        },
    }

    result = _utils.wrap_renderable_with_rich_config("Hello World", style_dict)

    rich_print(result)

    assert isinstance(result, _types.RichPanel)


def test_wrap_renderable_with_complex_background():
    """Test wrapping with complex background settings."""
    style_settings: _types.RichRenderableSettings = {
        "color": "blue",
        "background": {
            "box": "heavy",
            "title": "Complex Panel",
            "subtitle": "Subtitle",
            "title_align": "center",
            "expand": True,
            "padding": 2,
            "style": {"color": "white"},
            "border_style": {"color": "red", "bold": True},
        },
    }

    result = _utils.wrap_renderable_with_rich_config("Test content", style_settings)

    rich_print(result)

    assert isinstance(result, _types.RichPanel)


def test_rich_color_names():
    """Test that color name literals work."""
    # Test a few representative color names
    colors = ["red", "blue", "green", "yellow", "magenta", "cyan"]
    for color in colors:
        result = _utils.wrap_renderable_with_rich_config("Test", color)

        rich_print(result)

        assert isinstance(result, _types.RichText)


def test_rich_box_names():
    """Test that box name literals work."""
    boxes = ["ascii", "rounded", "double", "heavy", "minimal"]
    for box in boxes:
        style_settings: _types.RichRenderableSettings = {
            "background": {"box": box, "color": "white"}
        }
        result = _utils.wrap_renderable_with_rich_config("Test", style_settings)

        rich_print(result)

        assert isinstance(result, _types.RichPanel)


def test_empty_style_settings():
    """Test with empty style settings."""
    empty_style: _types.RichRenderableSettings = {}

    result = _utils.wrap_renderable_with_rich_config("Test", empty_style)

    rich_print(result)

    # With no styling, should return the original string or basic RichText
    assert isinstance(result, str) or isinstance(result, _types.RichText)


def test_non_string_renderable():
    """Test wrapping non-string renderables."""
    # Test with RichText object
    text = _types.RichText("Rich Text Object")
    style_settings: _types.RichRenderableSettings = {
        "color": "red",
        "background": {"color": "blue"},
    }
    result = _utils.wrap_renderable_with_rich_config(text, style_settings)

    rich_print(result)

    assert isinstance(result, _types.RichPanel)


def test_run_rich_live():
    """Test running a rich live renderable."""
    text = _types.RichText("Live Text", style=_types.RichStyle(color="green"))

    live_settings: _types.RichLiveSettings = {
        "duration": 0.1,  # Short duration for testing
        "refresh_rate": 10,
        "auto_refresh": True,
        "transient": False,
    }

    # This should run without error
    _utils.run_rich_live(text, live_settings)


def test_get_rich_console():
    """Test getting the rich console."""
    console = _utils.get_rich_console()
    assert isinstance(console, _types.RichConsole)


def test_has_rich_handler():
    """Test checking if a logger has a RichHandler."""
    # Create a logger without RichHandler
    logger = logging.getLogger("test_logger_no_rich")
    assert not _utils.has_rich_handler(logger)
    
    # Create a logger with RichHandler
    logger_with_rich = logging.getLogger("test_logger_with_rich")
    rich_handler = _utils.create_rich_handler({})
    logger_with_rich.addHandler(rich_handler)
    assert _utils.has_rich_handler(logger_with_rich)
    
    # Clean up
    logger_with_rich.removeHandler(rich_handler)


def test_create_rich_handler():
    """Test creating a RichHandler with settings."""
    settings: _types.RichLoggingSettings = {
        "show_time": True,
        "show_path": True,
        "show_level": False,
    }
    
    handler = _utils.create_rich_handler(settings)
    assert isinstance(handler, _utils.RichHandler)


def test_rich_logging_filter():
    """Test RichLoggingFilter functionality."""
    level_settings = {
        "error": {"level_style": "bold red", "message_style": "red"},
        "debug": {"level_style": "dim white", "message_style": "dim white"},
    }
    
    filter_obj = _utils.RichLoggingFilter(level_settings)
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    # Filter should return True and add rich config
    assert filter_obj.filter(record) is True
    assert hasattr(record, "_hammad_rich_config")
    assert record._hammad_rich_config == level_settings["error"]


def test_rich_logging_formatter():
    """Test RichLoggingFormatter functionality."""
    global_settings: _types.RichLoggingSettings = {
        "show_name": True,
        "show_level": True,
        "show_time": False,
    }
    
    formatter = _utils.RichLoggingFormatter(
        fmt="%(message)s",
        global_settings=global_settings,
    )
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    # Add rich config to record
    record._hammad_rich_config = {"level_style": "blue", "message_style": "white"}
    
    # Format the message
    formatted = formatter.formatMessage(record)
    assert isinstance(formatted, str)


def test_rich_plugin_error():
    """Test RichPluginError exception."""
    with pytest.raises(_utils.RichPluginError):
        raise _utils.RichPluginError("Test error message")


def test_error_handling_in_wrap_renderable():
    """Test error handling in wrap_renderable_with_rich_config."""
    # Test with invalid style that should fallback gracefully
    result = _utils.wrap_renderable_with_rich_config("Test", None)
    assert result == "Test"  # Should return original on error
    
    # Test with malformed dict that should fallback
    malformed_style = {"invalid_key": "invalid_value"}
    result = _utils.wrap_renderable_with_rich_config("Test", malformed_style)
    # Should still work or fallback gracefully
    assert result is not None


if __name__ == "__main__":
    pytest.main(["-v", __file__])
