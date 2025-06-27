import pytest
from hammad.cli import animate


def test_animate_flashing():
    """Test flashing animation."""
    # Should not raise any errors
    animate("Test flashing", type="flashing", duration=0.1)


def test_animate_pulsing():
    """Test pulsing animation."""
    # Should not raise any errors
    animate("Test pulsing", type="pulsing", duration=0.1)


def test_animate_shaking():
    """Test shaking animation."""
    # Should not raise any errors
    animate("Test shaking", type="shaking", duration=0.1)


def test_animate_typing():
    """Test typing animation."""
    # Should not raise any errors
    animate("Test typing", type="typing", duration=0.1)


def test_animate_spinning():
    """Test spinning animation."""
    # Should not raise any errors
    animate("Test spinning", type="spinning", duration=0.1)


def test_animate_rainbow():
    """Test rainbow animation."""
    # Should not raise any errors
    animate("Test rainbow", type="rainbow", duration=0.1)


def test_animate_with_custom_parameters():
    """Test animate with custom parameters."""
    # Test flashing with custom speed and colors
    animate("Test", type="flashing", duration=0.1, speed=0.2, colors=["red", "blue"])

    # Test pulsing with custom opacity
    animate("Test", type="pulsing", duration=0.1, min_opacity=0.1, max_opacity=0.9)

    # Test shaking with custom intensity
    animate("Test", type="shaking", duration=0.1, intensity=2, speed=0.05)

    # Test typing with custom speed
    animate("Test", type="typing", duration=0.1, speed=0.01)

    # Test spinning with custom frames
    animate("Test", type="spinning", duration=0.1, frames=[".", "o", "O"], prefix=False)

    # Test rainbow with custom colors
    animate(
        "Test", type="rainbow", duration=0.1, speed=0.2, colors=["red", "green", "blue"]
    )


def test_animate_invalid_type():
    """Test animate with invalid animation type."""
    with pytest.raises(ValueError, match="Unknown animation type"):
        animate("Test", type="invalid_type", duration=0.1)


def test_animate_no_duration():
    """Test animate without specifying duration (should use default)."""
    # Should not raise any errors and use default duration
    animate("Test", type="flashing", speed=0.1)  # Quick test with fast speed


if __name__ == "__main__":
    pytest.main(["-v", __file__])
