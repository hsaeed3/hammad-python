import pytest
from hammad.types.color import Color, ColorName, RGBColor, HexColor


class TestColor:
    """Test cases for the Color class."""

    def test_create_from_name(self):
        """Test creating color from color name."""
        color = Color.create("blue")
        assert str(color) == "blue"
        assert color.rich_color.name == "blue"

    def test_create_from_hex(self):
        """Test creating color from hex string."""
        color = Color.create("#ff0000")
        assert str(color) == "#ff0000"

        color2 = Color.create("#FF0000")
        assert str(color2) == "#ff0000"

    def test_create_from_rgb(self):
        """Test creating color from RGB tuple."""
        color = Color.create((255, 0, 0))
        assert str(color) == "#ff0000"
        assert color.rich_color.get_truecolor().red == 255
        assert color.rich_color.get_truecolor().green == 0
        assert color.rich_color.get_truecolor().blue == 0

    def test_from_name_classmethod(self):
        """Test from_name class method."""
        color = Color.from_name("red")
        assert str(color) == "red"

    def test_from_hex_classmethod(self):
        """Test from_hex class method."""
        color = Color.from_hex("#00ff00")
        assert str(color) == "#00ff00"

    def test_from_rgb_classmethod(self):
        """Test from_rgb class method."""
        color = Color.from_rgb((0, 255, 0))
        assert str(color) == "#00ff00"

    def test_caching(self):
        """Test that color instances are cached."""
        color1 = Color.create("blue")
        color2 = Color.create("blue")
        assert color1 is color2

        color3 = Color.create((255, 0, 0))
        color4 = Color.create((255, 0, 0))
        assert color3 is color4

    def test_wrap_basic(self):
        """Test basic text wrapping functionality."""
        color = Color.create("red")
        text = color.wrap("Hello, World!")
        assert str(text) == "Hello, World!"
        assert text.style.color == color.rich_color

    def test_wrap_with_styles(self):
        """Test text wrapping with additional styles."""
        color = Color.create("blue")
        text = color.wrap("Bold text", bold=True)
        assert str(text) == "Bold text"
        assert text.style.bold is True
        assert text.style.color == color.rich_color

    def test_rich_color_property(self):
        """Test rich_color property access."""
        color = Color.create("green")
        rich_color = color.rich_color
        assert rich_color.name == "green"

    def test_pydantic_color_names(self):
        """Test colors that exist in Pydantic but not Rich."""
        color = Color.create("aliceblue")
        # Should return hex since it's a pydantic-only color
        assert str(color).startswith("#")

    def test_invalid_color_type(self):
        """Test error handling for invalid color types."""
        with pytest.raises(ValueError, match="Invalid color type"):
            Color.create(123)

    def test_string_representation_consistency(self):
        """Test that string representation is consistent."""
        # Rich color names should return the name
        rich_color = Color.create("red")
        assert str(rich_color) == "red"

        # Hex colors should return lowercase hex
        hex_color = Color.create("#FF0000")
        assert str(hex_color) == "#ff0000"

        # RGB tuples should return hex
        rgb_color = Color.create((255, 0, 0))
        assert str(rgb_color) == "#ff0000"

    def test_style_caching(self):
        """Test that styles are cached when same parameters are used."""
        color = Color.create("blue")

        # First call creates style
        text1 = color.wrap("test", bold=True)
        style1 = color._style

        # Second call with same parameters should reuse style
        text2 = color.wrap("test2", bold=True)
        style2 = color._style
        assert style1 is style2

        # Different parameters should create new style
        text3 = color.wrap("test3", italic=True)
        style3 = color._style
        assert style1 is not style3


class TestColorTypes:
    """Test color type aliases and validation."""

    def test_hex_color_type(self):
        """Test HexColor type alias."""
        hex_color: HexColor = "#ff0000"
        color = Color.create(hex_color)
        assert str(color) == "#ff0000"

    def test_rgb_color_type(self):
        """Test RGBColor type alias."""
        rgb_color: RGBColor = (255, 0, 0)
        color = Color.create(rgb_color)
        assert str(color) == "#ff0000"

    def test_color_name_type(self):
        """Test ColorName type alias."""
        color_name: ColorName = "blue"
        color = Color.create(color_name)
        assert str(color) == "blue"


class TestColorPerformance:
    """Test color performance optimizations."""

    def test_cache_hit(self):
        """Test cache performance."""
        # First creation
        color1 = Color.create("red")

        # Should hit cache
        color2 = Color.create("red")
        assert color1 is color2

    def test_immediate_rich_color_initialization(self):
        """Test that rich color is initialized immediately."""
        color = Color.create("blue")
        assert color._rich_color is not None
        assert color._rich_color.name == "blue"
