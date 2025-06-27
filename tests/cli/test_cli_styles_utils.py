import pytest
from hammad.cli.styles import utils


def test_cli_error():
    """Test CLIStyleError exception."""
    from hammad.cli.styles.types import CLIStyleError

    error = CLIStyleError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_live_render_invalid_renderable():
    """Test live_render with invalid renderable."""
    from hammad.cli.styles.types import CLIStyleError

    with pytest.raises(CLIStyleError, match="The renderable must be a RenderableType"):
        utils.live_render(123, {})


def test_live_render_with_settings():
    """Test live_render with valid settings."""
    from rich.text import Text

    renderable = Text("Test")
    settings = {
        "duration": 0.1,
        "refresh_rate": 10,
        "auto_refresh": True,
        "transient": False,
        "redirect_stdout": True,
        "redirect_stderr": True,
        "vertical_overflow": "ellipsis",
    }

    # Should not raise an exception
    utils.live_render(renderable, settings)


def test_style_renderable_with_string_style():
    """Test style_renderable with string style."""
    from rich.text import Text

    result = utils.style_renderable("Hello", style="red")
    assert isinstance(result, Text)


def test_style_renderable_with_tuple_style():
    """Test style_renderable with tuple color."""
    from rich.text import Text

    result = utils.style_renderable("Hello", style=(255, 0, 0))
    assert isinstance(result, Text)


def test_style_renderable_with_dict_style():
    """Test style_renderable with dict style settings."""
    from rich.text import Text

    style = {"color": "blue", "bold": True, "italic": True}
    result = utils.style_renderable("Hello", style=style)
    assert isinstance(result, Text)


def test_style_renderable_with_bg():
    """Test style_renderable with bg parameter."""
    from rich.panel import Panel

    result = utils.style_renderable("Hello", bg="yellow")
    assert isinstance(result, Panel)


def test_style_renderable_with_bg_settings():
    """Test style_renderable with bg_settings parameter."""
    from rich.panel import Panel

    bg_settings = {"title": "Test Panel", "box": "rounded", "padding": 1}
    result = utils.style_renderable("Hello", bg="yellow", bg_settings=bg_settings)
    assert isinstance(result, Panel)


def test_style_renderable_with_complex_bg_settings():
    """Test style_renderable with complex bg_settings."""
    from rich.panel import Panel

    bg_settings = {
        "title": "Complex Panel",
        "subtitle": "Subtitle",
        "expand": True,
        "padding": 1,
        "style": {"color": "white"},
        "border_style": {"color": "red", "bold": True},
    }
    result = utils.style_renderable("Hello", bg="blue", bg_settings=bg_settings)
    assert isinstance(result, Panel)


def test_style_renderable_fallback():
    """Test style_renderable fallback behavior."""
    # Should return original renderable if processing fails
    result = utils.style_renderable("Hello")
    assert result == "Hello"


def test_style_renderable_with_invalid_style():
    """Test style_renderable with invalid style."""
    # Should fallback gracefully
    result = utils.style_renderable("Hello", style=123)
    assert result == "Hello"


def test_live_render_default_settings():
    """Test live_render with minimal settings (uses defaults)."""
    from rich.text import Text

    renderable = Text("Test")
    settings = {}  # Empty settings should use defaults

    # Should not raise an exception and use default values
    utils.live_render(renderable, settings)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
