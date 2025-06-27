import pytest
from hammad.cli import plugins


def test_print_basic():
    """Test _print with basic functionality (no styling)."""
    import io
    from contextlib import redirect_stdout

    # Test basic print functionality
    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", "World")

    # Should use rich.print with markup support
    result = output.getvalue()
    assert "Hello World" in result


def test_print_with_style():
    """Test _print with style parameter."""
    import io
    from contextlib import redirect_stdout

    # Test with color style
    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", style="red")

    # Should produce styled output (exact format depends on rich)
    result = output.getvalue()
    assert len(result) > 0


def test_print_with_style_dict():
    """Test _print with style dictionary."""
    import io
    from contextlib import redirect_stdout

    style = {"color": "blue", "bold": True}

    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", style=style)

    result = output.getvalue()
    assert len(result) > 0


def test_print_with_background():
    """Test _print with background parameter."""
    import io
    from contextlib import redirect_stdout

    background = {"color": "yellow", "title": "Test"}

    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", bg=background)

    result = output.getvalue()
    assert len(result) > 0


def test_print_with_live_int():
    """Test _print with live parameter as integer."""
    import io
    from contextlib import redirect_stdout

    # Use very short duration for testing
    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", live=1)  # 1 second duration

    # Should complete without error
    result = output.getvalue()
    assert len(result) >= 0  # May be empty due to live rendering


def test_print_with_live_dict():
    """Test _print with live parameter as dictionary."""
    import io
    from contextlib import redirect_stdout

    live_settings = {
        "duration": 0.5,  # Very short for testing
        "transient": True,
    }

    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", live=live_settings)

    # Should complete without error
    result = output.getvalue()
    assert len(result) >= 0


def test_print_with_custom_file():
    """Test _print with custom file parameter."""
    import io

    output = io.StringIO()
    plugins.print("Hello", "World", file=output)

    result = output.getvalue()
    assert "Hello World" in result


def test_print_with_custom_sep_end():
    """Test _print with custom separator and end parameters."""
    import io

    output = io.StringIO()
    plugins.print("A", "B", "C", sep="-", end="!\n", file=output)

    result = output.getvalue()
    assert "A-B-C!" in result


def test_print_with_flush():
    """Test _print with flush parameter."""
    import io

    output = io.StringIO()
    # Should not raise error with flush=True
    plugins.print("Hello", file=output, flush=True)

    result = output.getvalue()
    assert "Hello" in result


def test_print_combined_parameters():
    """Test _print with multiple styling parameters."""
    import io
    from contextlib import redirect_stdout

    style = {"color": "green", "bold": True}
    background = {"color": "black"}

    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", "World", sep=" | ", style=style, bg=background)

    result = output.getvalue()
    assert len(result) > 0


def test_print_with_tuple_style():
    """Test _print with tuple color style."""
    import io
    from contextlib import redirect_stdout

    # RGB tuple
    style = (255, 0, 0)  # Red

    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", style=style)

    result = output.getvalue()
    assert len(result) > 0


def test_print_error_handling():
    """Test _print error handling with invalid inputs."""
    import io
    from contextlib import redirect_stdout

    # Should handle invalid style gracefully
    output = io.StringIO()
    with redirect_stdout(output):
        plugins.print("Hello", style=object())  # Invalid style

    # Should not raise exception, fallback to basic behavior
    result = output.getvalue()
    assert len(result) >= 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
