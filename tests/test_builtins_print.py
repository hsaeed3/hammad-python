import pytest
from hammad._builtins._print import print as hammad_print


def test_basic_print(capsys):
    """Test basic print functionality without styling."""
    hammad_print("Hello", "World")
    captured = capsys.readouterr()
    assert "Hello World" in captured.out


def test_print_with_sep(capsys):
    """Test print with custom separator."""
    hammad_print("A", "B", "C", sep="-")
    captured = capsys.readouterr()
    assert "A-B-C" in captured.out


def test_print_with_end(capsys):
    """Test print with custom end character."""
    hammad_print("Hello", end="!")
    captured = capsys.readouterr()
    assert captured.out.endswith("!")


def test_print_with_string_style(capsys):
    """Test print with string style parameter."""
    hammad_print("Styled text", style="red")
    captured = capsys.readouterr()
    assert "Styled text" in captured.out


def test_print_with_tuple_color_style(capsys):
    """Test print with tuple color style."""
    hammad_print("Colored text", style=(255, 0, 0))
    captured = capsys.readouterr()
    assert "Colored text" in captured.out


def test_print_with_style_dict(capsys):
    """Test print with style dictionary."""
    style_dict = {"color": "blue", "bold": True}
    hammad_print("Bold blue text", style=style_dict)
    captured = capsys.readouterr()
    assert "Bold blue text" in captured.out


def test_print_with_background(capsys):
    """Test print with background parameter."""
    hammad_print("Background text", bg="yellow")
    captured = capsys.readouterr()
    assert "Background text" in captured.out


def test_print_with_background_dict(capsys):
    """Test print with background dictionary."""
    bg_dict = {"color": "green", "title": "Test Box"}
    hammad_print("Boxed text", bg=bg_dict)
    captured = capsys.readouterr()
    assert "Boxed text" in captured.out


def test_print_with_live_integer(capsys):
    """Test print with live rendering (integer duration)."""
    hammad_print("Live text", live=1)
    captured = capsys.readouterr()
    assert "Live text" in captured.out


def test_print_with_live_dict(capsys):
    """Test print with live settings dictionary."""
    live_settings = {"duration": 0.1, "transient": False, "refresh_rate": 10}
    hammad_print("Live dict text", live=live_settings)
    captured = capsys.readouterr()
    assert "Live dict text" in captured.out


def test_print_multiple_values_with_styling(capsys):
    """Test print with multiple values and styling."""
    hammad_print("Value1", "Value2", "Value3", sep=" | ", style="cyan")
    captured = capsys.readouterr()
    assert "Value1 | Value2 | Value3" in captured.out


def test_print_combined_styling(capsys):
    """Test print with both style and background."""
    hammad_print("Combined styling", style="bold red", bg="white")
    captured = capsys.readouterr()
    assert "Combined styling" in captured.out


def test_print_empty_values(capsys):
    """Test print with empty values."""
    hammad_print()
    captured = capsys.readouterr()
    assert captured.out == "\n"


def test_print_none_values(capsys):
    """Test print with None values."""
    hammad_print(None, "text", None)
    captured = capsys.readouterr()
    assert "None text None" in captured.out


def test_print_numeric_values(capsys):
    """Test print with numeric values."""
    hammad_print(42, 3.14, True, sep=", ")
    captured = capsys.readouterr()
    assert "42, 3.14, True" in captured.out


def test_print_with_file_parameter(tmpfile=None):
    """Test print with file parameter."""
    import io

    buffer = io.StringIO()
    hammad_print("File output", file=buffer)
    buffer.seek(0)
    content = buffer.read()
    assert "File output" in content


def test_print_with_flush_parameter(capsys):
    """Test print with flush parameter."""
    hammad_print("Flushed output", flush=True)
    captured = capsys.readouterr()
    assert "Flushed output" in captured.out


if __name__ == "__main__":
    pytest.main(["-v", __file__])
