import pytest
from hammad.types.color import Color

def test_color_from_name():
    """Test creating colors from color names."""
    color = Color.from_name("blue")
    assert str(color) == "blue"
    
    color = Color.from_name("red")
    assert str(color) == "red"


def test_color_from_hex():
    """Test creating colors from hex values."""
    color = Color.from_hex("#FF0000")
    assert str(color) == "#ff0000"
    
    color = Color.from_hex("#00FF00")
    assert str(color) == "#00ff00"


def test_color_from_rgb():
    """Test creating colors from RGB tuples."""
    color = Color.from_rgb((255, 0, 0))
    assert str(color) == "#ff0000"
    
    color = Color.from_rgb((0, 255, 0))
    assert str(color) == "#00ff00"


def test_color_create():
    """Test the create factory method."""
    # Test with color name
    color1 = Color.create("blue")
    assert str(color1) == "blue"
    
    # Test with hex
    color2 = Color.create("#FF0000")
    assert str(color2) == "#ff0000"
    
    # Test with RGB tuple
    color3 = Color.create((0, 255, 0))
    assert str(color3) == "#00ff00"


def test_color_caching():
    """Test that colors are cached properly."""
    color1 = Color.create("blue")
    color2 = Color.create("blue")
    assert color1 is color2  # Should be the same instance due to caching


def test_color_tag():
    """Test the tag method for styling text."""
    color = Color.from_name("blue")
    text = color.tag("Hello, World!")
    assert str(text) == "Hello, World!"
    
    # Test with styling options
    bold_text = color.tag("Bold text", bold=True)
    assert str(bold_text) == "Bold text"


def test_color_rich_color_property():
    """Test accessing the rich color property."""
    color = Color.from_name("blue")
    rich_color = color.rich_color
    assert rich_color is not None
    assert str(rich_color) == "blue"


def test_invalid_color_type():
    """Test that invalid color types raise ValueError."""
    with pytest.raises(ValueError, match="Invalid color type"):
        Color.create(123)  # Invalid type


def test_pydantic_color_names():
    """Test that pydantic color names work correctly."""
    color = Color.from_name("aliceblue")
    assert str(color) == "#f0f8ff"


def test_rich_color_names():
    """Test that rich color names work correctly."""
    color = Color.from_name("bright_red")
    assert str(color) == "bright_red"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])