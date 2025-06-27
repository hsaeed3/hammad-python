import pytest
from hammad.cli import plugins


def test_input_basic():
    """Test basic input functionality."""
    import io
    from unittest.mock import patch

    # Mock built-in input for basic case
    with patch("builtins.input", return_value="test input"):
        result = plugins.input("Enter text: ")

    assert result == "test input"


def test_input_with_string_schema():
    """Test input with string schema."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="hello"):
        result = plugins.input("Enter text: ", schema=str)

    assert result == "hello"
    assert isinstance(result, str)


def test_input_with_int_schema():
    """Test input with integer schema."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="42"):
        result = plugins.input("Enter number: ", schema=int)

    assert result == 42
    assert isinstance(result, int)


def test_input_with_float_schema():
    """Test input with float schema."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="3.14"):
        result = plugins.input("Enter float: ", schema=float)

    assert result == 3.14
    assert isinstance(result, float)


def test_input_with_bool_schema():
    """Test input with boolean schema using Confirm.ask."""
    from unittest.mock import patch

    with patch("rich.prompt.Confirm.ask", return_value=True):
        result = plugins.input("Confirm: ", schema=bool)

    assert result is True
    assert isinstance(result, bool)


def test_input_with_dict_schema():
    """Test input with dict schema (JSON parsing)."""
    from unittest.mock import patch

    json_input = '{"key": "value", "number": 42}'
    with patch("rich.prompt.Prompt.ask", return_value=json_input):
        result = plugins.input("Enter JSON: ", schema=dict)

    assert result == {"key": "value", "number": 42}
    assert isinstance(result, dict)


def test_input_with_list_schema():
    """Test input with list schema (JSON parsing)."""
    from unittest.mock import patch

    json_input = '[1, 2, 3, "test"]'
    with patch("rich.prompt.Prompt.ask", return_value=json_input):
        result = plugins.input("Enter list: ", schema=list)

    assert result == [1, 2, 3, "test"]
    assert isinstance(result, list)


def test_input_with_style():
    """Test input with style parameter."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="styled input"):
        result = plugins.input("Enter text: ", style="red")

    assert result == "styled input"


def test_input_with_bg():
    """Test input with background parameter."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="bg input"):
        result = plugins.input("Enter text: ", bg="yellow")

    assert result == "bg input"


def test_input_with_password():
    """Test input with password mode."""
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="secret"):
        result = plugins.input("Password: ", password=True)

    assert result == "secret"


def test_input_with_completion():
    """Test input with completion options."""
    from unittest.mock import patch

    with patch("prompt_toolkit.prompt", return_value="option1"):
        result = plugins.input("Choose: ", complete=["option1", "option2", "option3"])

    assert result == "option1"


def test_input_with_custom_validation():
    """Test input with custom validation function."""
    from unittest.mock import patch

    def validate_even(value):
        return int(value) % 2 == 0

    with patch("rich.prompt.Prompt.ask", return_value="4"):
        result = plugins.input("Enter even number: ", validate=validate_even)

    assert result == "4"


def test_input_validation_error():
    """Test input validation error handling."""
    from unittest.mock import patch
    from hammad.cli.plugins import InputError

    with patch("rich.prompt.Prompt.ask", return_value="not_a_number"):
        with pytest.raises(InputError):
            plugins.input("Enter number: ", schema=int)


def test_input_json_validation_error():
    """Test input JSON validation error."""
    from unittest.mock import patch
    from hammad.cli.plugins import InputError

    with patch("rich.prompt.Prompt.ask", return_value="invalid json"):
        with pytest.raises(InputError):
            plugins.input("Enter JSON: ", schema=dict)


def test_input_bool_string_conversion():
    """Test input boolean string conversion."""
    from unittest.mock import patch

    # Test boolean confirmation with Confirm.ask
    with patch("rich.prompt.Confirm.ask", return_value=True):
        result = plugins.input("Boolean: ", schema=bool)
        assert result is True
        assert isinstance(result, bool)

    with patch("rich.prompt.Confirm.ask", return_value=False):
        result = plugins.input("Boolean: ", schema=bool)
        assert result is False
        assert isinstance(result, bool)


def test_input_error_class():
    """Test InputError exception class."""
    from hammad.cli.plugins import InputError

    error = InputError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)


def test_input_keyboard_interrupt():
    """Test input handling of KeyboardInterrupt."""
    from unittest.mock import patch

    # Mock builtins.input since basic input goes through that path
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            plugins.input("Enter text: ")


def test_input_optional_schema():
    """Test input with optional schema (Union with None)."""
    from typing import Optional
    from unittest.mock import patch

    with patch("rich.prompt.Prompt.ask", return_value="none"):
        result = plugins.input("Optional text: ", schema=Optional[str])

    assert result is None


def test_input_with_style_dict():
    """Test input with style dictionary."""
    from unittest.mock import patch

    style = {"color": "blue", "bold": True}
    with patch("rich.prompt.Prompt.ask", return_value="styled"):
        result = plugins.input("Enter: ", style=style)

    assert result == "styled"


def test_input_fallback_behavior():
    """Test input fallback behavior on errors."""
    from unittest.mock import patch

    # Test that input gracefully handles styling errors
    with patch("rich.prompt.Prompt.ask", return_value="fallback"):
        result = plugins.input("Enter: ", style=object())  # Invalid style

    assert result == "fallback"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
