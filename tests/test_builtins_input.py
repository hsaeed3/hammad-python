import pytest
from hammad._builtins._input import input as hammad_input


def test_basic_input_string(monkeypatch):
    """Test basic input functionality returning string."""
    monkeypatch.setattr("builtins.input", lambda _: "test input")
    result = hammad_input("Enter text: ")
    assert result == "test input"


def test_input_with_int_schema(monkeypatch):
    """Test input with integer schema validation."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "42")
    result = hammad_input("Enter number: ", schema=int)
    assert result == 42
    assert isinstance(result, int)


def test_input_with_float_schema(monkeypatch):
    """Test input with float schema validation."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "3.14")
    result = hammad_input("Enter float: ", schema=float)
    assert result == 3.14
    assert isinstance(result, float)


def test_input_with_bool_schema(monkeypatch):
    """Test input with boolean schema using Confirm.ask."""
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda _: True)
    result = hammad_input("Confirm: ", schema=bool)
    assert result is True


def test_input_with_dict_schema(monkeypatch):
    """Test input with dictionary schema validation."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: '{"key": "value"}')
    result = hammad_input("Enter JSON: ", schema=dict)
    assert result == {"key": "value"}
    assert isinstance(result, dict)


def test_input_with_list_schema(monkeypatch):
    """Test input with list schema validation."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "[1, 2, 3]")
    result = hammad_input("Enter list: ", schema=list)
    assert result == [1, 2, 3]
    assert isinstance(result, list)


def test_input_with_string_style(monkeypatch):
    """Test input with string style parameter."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "styled input")
    result = hammad_input("Enter text: ", style="blue")
    assert result == "styled input"


def test_input_with_tuple_color_style(monkeypatch):
    """Test input with tuple color style."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "colored input")
    result = hammad_input("Enter text: ", style=(0, 255, 0))
    assert result == "colored input"


def test_input_with_background_style(monkeypatch):
    """Test input with background style parameter."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "bg input")
    result = hammad_input("Enter text: ", bg="red")
    assert result == "bg input"


def test_input_password_mode(monkeypatch):
    """Test input in password mode."""
    monkeypatch.setattr(
        "rich.prompt.Prompt.ask",
        lambda _, password=False: "secret" if password else "not secret",
    )
    result = hammad_input("Password: ", password=True)
    assert result == "secret"


def test_input_multiline_mode(monkeypatch):
    """Test input in multiline mode."""

    # Mock prompt_toolkit prompt to simulate multiline input
    def mock_pt_prompt(prompt_text):
        if prompt_text == "... ":
            # Simulate entering lines and then empty line to finish
            if not hasattr(mock_pt_prompt, "call_count"):
                mock_pt_prompt.call_count = 0
            mock_pt_prompt.call_count += 1
            if mock_pt_prompt.call_count == 1:
                return "line 1"
            elif mock_pt_prompt.call_count == 2:
                return "line 2"
            else:
                return ""  # Empty line to finish
        return ""

    monkeypatch.setattr("hammad._builtins._input.pt_prompt", mock_pt_prompt)
    monkeypatch.setattr("rich.console.Console.print", lambda *args, **kwargs: None)

    result = hammad_input("Enter multiline: ", multiline=True)
    assert result == "line 1\nline 2"


def test_input_with_completion(monkeypatch):
    """Test input with completion options."""
    monkeypatch.setattr(
        "hammad._builtins._input.pt_prompt", lambda _, completer=None: "completed"
    )
    result = hammad_input("Choose: ", complete=["option1", "option2", "option3"])
    assert result == "completed"


def test_input_with_validation_success(monkeypatch):
    """Test input with custom validation that passes."""

    def validate_func(value):
        return len(value) > 3

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "valid")
    result = hammad_input("Enter text: ", validate=validate_func)
    assert result == "valid"


def test_input_with_validation_failure(monkeypatch):
    """Test input with custom validation that fails."""

    def validate_func(value):
        return len(value) > 10

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "short")

    with pytest.raises(Exception):  # Should raise InputError or similar
        hammad_input("Enter text: ", validate=validate_func)


def test_input_keyboard_interrupt(monkeypatch):
    """Test input handling keyboard interrupt."""

    def mock_prompt(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", mock_prompt)
    monkeypatch.setattr("rich.console.Console.print", lambda *args, **kwargs: None)

    with pytest.raises(KeyboardInterrupt):
        hammad_input("Enter text: ")


def test_input_int_convenience_function(monkeypatch):
    """Test input_int convenience function."""
    from hammad._builtins._input import input_int

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "123")
    result = input_int("Enter integer: ")
    assert result == 123
    assert isinstance(result, int)


def test_input_float_convenience_function(monkeypatch):
    """Test input_float convenience function."""
    from hammad._builtins._input import input_float

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "12.34")
    result = input_float("Enter float: ")
    assert result == 12.34
    assert isinstance(result, float)


def test_input_bool_convenience_function(monkeypatch):
    """Test input_bool convenience function."""
    from hammad._builtins._input import input_bool

    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda _: False)
    result = input_bool("Confirm: ")
    assert result is False


def test_input_json_convenience_function(monkeypatch):
    """Test input_json convenience function."""
    from hammad._builtins._input import input_json

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: '{"test": true}')
    result = input_json("Enter JSON: ")
    assert result == {"test": True}
    assert isinstance(result, dict)


def test_input_confirm_convenience_function(monkeypatch):
    """Test input_confirm convenience function."""
    from hammad._builtins._input import input_confirm

    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda _, default=False: default)
    result = input_confirm("Continue?", default=True)
    assert result is True


def test_input_error_exception():
    """Test InputError exception creation."""
    from hammad._builtins._input import InputError

    error = InputError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)


def test_validate_against_schema_string():
    """Test _validate_against_schema with string type."""
    from hammad._builtins._input import _validate_against_schema

    result = _validate_against_schema("test", str)
    assert result == "test"


def test_validate_against_schema_int():
    """Test _validate_against_schema with int type."""
    from hammad._builtins._input import _validate_against_schema

    result = _validate_against_schema("42", int)
    assert result == 42


def test_validate_against_schema_invalid_int():
    """Test _validate_against_schema with invalid int."""
    from hammad._builtins._input import _validate_against_schema, InputError

    with pytest.raises(InputError):
        _validate_against_schema("not_a_number", int)


def test_validate_against_schema_bool_true():
    """Test _validate_against_schema with bool type (true values)."""
    from hammad._builtins._input import _validate_against_schema

    for value in ["true", "t", "yes", "y", "1", "on"]:
        result = _validate_against_schema(value, bool)
        assert result is True


def test_validate_against_schema_bool_false():
    """Test _validate_against_schema with bool type (false values)."""
    from hammad._builtins._input import _validate_against_schema

    for value in ["false", "f", "no", "n", "0", "off"]:
        result = _validate_against_schema(value, bool)
        assert result is False


def test_validate_against_schema_invalid_json():
    """Test _validate_against_schema with invalid JSON for dict."""
    from hammad._builtins._input import _validate_against_schema, InputError

    with pytest.raises(InputError):
        _validate_against_schema("not valid json", dict)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
