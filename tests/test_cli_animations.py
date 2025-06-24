import pytest
from hammad.cli.animations import (
    animate_flashing,
    animate_pulsing,
    animate_rainbow,
    animate_shaking,
    animate_spinning,
    animate_typing,
)


def test_animate_flashing():
    """Test that animate_flashing runs without errors."""
    # Test with string
    animate_flashing("Test Flash", duration=0.1)

    # Test with custom parameters
    animate_flashing(
        "Alert!", duration=0.1, speed=0.1, on_color="red", off_color="dark_red"
    )


def test_animate_pulsing():
    """Test that animate_pulsing runs without errors."""
    # Test with string
    animate_pulsing("Test Pulse", duration=0.1)

    # Test with custom parameters
    animate_pulsing(
        "Loading...", duration=0.1, speed=2.0, min_opacity=0.3, max_opacity=1.0
    )


def test_animate_rainbow():
    """Test that animate_rainbow runs without errors."""
    # Test with string
    animate_rainbow("Rainbow Text", duration=0.1)

    # Test with custom speed
    animate_rainbow("Colorful!", duration=0.1, speed=0.5)


def test_animate_shaking():
    """Test that animate_shaking runs without errors."""
    # Test with string
    animate_shaking("Shake!", duration=0.1)

    # Test with custom parameters
    animate_shaking("Error!", duration=0.1, intensity=3, speed=10.0)


def test_animate_spinning():
    """Test that animate_spinning runs without errors."""
    # Test with string
    animate_spinning("Processing...", duration=0.1)

    # Test with custom parameters
    animate_spinning(
        "Loading", duration=0.1, frames=["◐", "◓", "◑", "◒"], speed=0.1, prefix=False
    )


def test_animate_typing():
    """Test that animate_typing runs without errors."""
    # Test with basic string
    animate_typing("Hello, World!", duration=0.1)

    # Test with custom parameters
    animate_typing(
        "Fast typing", duration=0.1, typing_speed=0.05, cursor="|", show_cursor=False
    )


def test_animation_with_empty_string():
    """Test animations with empty strings."""
    animate_flashing("", duration=0.1)
    animate_pulsing("", duration=0.1)
    animate_rainbow("", duration=0.1)
    animate_shaking("", duration=0.1)
    animate_spinning("", duration=0.1)
    animate_typing("", duration=0.1)


def test_animation_with_special_characters():
    """Test animations with special characters."""
    special_text = "Hello! @#$%^&*()_+ 🌟"
    animate_flashing(special_text, duration=0.1)
    animate_pulsing(special_text, duration=0.1)
    animate_rainbow(special_text, duration=0.1)
    animate_shaking(special_text, duration=0.1)
    animate_spinning(special_text, duration=0.1)
    animate_typing(special_text, duration=0.1)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
