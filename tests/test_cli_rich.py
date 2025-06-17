import pytest
from hammad._internal import _rich
from rich import print as rich_print



def test_rich_color_tuple_type():
    """Test RichColorTuple type alias."""
    # This is a type alias, so we can't directly test it
    # but we can verify it works with type checking
    color: _rich.RichColorTuple = (255, 128, 0)
    assert color == (255, 128, 0)


def test_rich_color_hex_type():
    """Test RichColorHex type alias."""
    color: _rich.RichColorHex = "#ff8000"
    assert color == "#ff8000"


def test_rich_style_settings():
    """Test RichStyleSettings TypedDict."""
    style: _rich.RichStyleSettings = {
        "color": "red",
        "bold": True,
        "italic": False
    }
    assert style["color"] == "red"
    assert style["bold"] is True
    assert style["italic"] is False


def test_rich_background_settings():
    """Test RichBackgroundSettings TypedDict."""
    bg: _rich.RichBackgroundSettings = {
        "color": "blue",
        "box": "rounded",
        "title": "Test Title",
        "padding": 1
    }
    assert bg["color"] == "blue"
    assert bg["box"] == "rounded"
    assert bg["title"] == "Test Title"
    assert bg["padding"] == 1


def test_wrap_renderable_with_string_style():
    """Test wrapping a renderable with string style."""
    result = _rich.wrap_renderable_with_rich_config(
        "Hello World",
        style="red",
        bg="blue"
    )

    rich_print(result)

    # Should return a Panel containing styled text
    assert isinstance(result, _rich.RichPanel)


def test_wrap_renderable_with_tuple_color():
    """Test wrapping a renderable with tuple color."""
    result = _rich.wrap_renderable_with_rich_config(
        "Hello World",
        style=(255, 0, 0),  # Red RGB
        bg=(0, 0, 255)      # Blue RGB
    )

    rich_print(result)

    assert isinstance(result, _rich.RichPanel)


def test_wrap_renderable_with_dict_style():
    """Test wrapping a renderable with dictionary style."""
    style_dict: _rich.RichStyleSettings = {
        "color": "green",
        "bold": True,
        "italic": True
    }
    bg_dict: _rich.RichBackgroundSettings = {
        "color": "yellow",
        "box": "double",
        "title": "Test Panel"
    }
    
    result = _rich.wrap_renderable_with_rich_config(
        "Hello World",
        style=style_dict,
        bg=bg_dict
    )

    rich_print(result)

    assert isinstance(result, _rich.RichPanel)


def test_wrap_renderable_with_complex_background():
    """Test wrapping with complex background settings."""
    bg_settings: _rich.RichBackgroundSettings = {
        "box": "heavy",
        "title": "Complex Panel",
        "subtitle": "Subtitle",
        "title_align": "center",
        "expand": True,
        "padding": 2,
        "style": {
            "color": "white"
        },
        "border_style": {
            "color": "red",
            "bold": True
        }
    }
    
    result = _rich.wrap_renderable_with_rich_config(
        "Test content",
        style="blue",
        bg=bg_settings
    )

    rich_print(result)

    assert isinstance(result, _rich.RichPanel)


def test_rich_color_names():
    """Test that color name literals work."""
    # Test a few representative color names
    colors = ["red", "blue", "green", "yellow", "magenta", "cyan"]
    for color in colors:
        result = _rich.wrap_renderable_with_rich_config(
            "Test",
            style=color,
            bg="black"
        )

        rich_print(result)

        assert isinstance(result, _rich.RichPanel)


def test_rich_box_names():
    """Test that box name literals work."""
    boxes = ["ascii", "rounded", "double", "heavy", "minimal"]
    for box in boxes:
        bg_settings: _rich.RichBackgroundSettings = {
            "box": box,
            "color": "white"
        }
        result = _rich.wrap_renderable_with_rich_config(
            "Test",
            style="black",
            bg=bg_settings
        )

        rich_print(result)

        assert isinstance(result, _rich.RichPanel)


def test_empty_style_settings():
    """Test with empty style settings."""
    empty_style: _rich.RichStyleSettings = {}
    empty_bg: _rich.RichBackgroundSettings = {}
    
    result = _rich.wrap_renderable_with_rich_config(
        "Test",
        style=empty_style,
        bg=empty_bg
    )

    rich_print(result)

    assert isinstance(result, _rich.RichPanel)


def test_non_string_renderable():
    """Test wrapping non-string renderables."""
    # Test with RichText object
    text = _rich.RichText("Rich Text Object")
    result = _rich.wrap_renderable_with_rich_config(
        text,
        style="red",
        bg="blue"
    )

    rich_print(result)

    assert isinstance(result, _rich.RichPanel)


if __name__ == "__main__":
    pytest.main(
        ['-v', __file__]
    )

