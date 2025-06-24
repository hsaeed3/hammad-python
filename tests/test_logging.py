import pytest
from hammad.logging import (
    Logger,
    get_logger,
    trace,
    trace_cls,
    trace_function,
)


def test_logger_basic_creation():
    """Test basic logger creation and configuration."""
    logger = get_logger("test_logger")
    assert logger.name == "test_logger"
    assert isinstance(logger, Logger)


def test_logger_with_custom_level():
    """Test logger with custom logging level."""
    logger = get_logger("test_logger", level="info")
    assert logger.level == "info"


def test_logger_rich_and_plain():
    """Test logger with rich and plain formatting."""
    rich_logger = get_logger("rich_test", rich=True)
    plain_logger = get_logger("plain_test", rich=False)

    assert len(rich_logger.handlers) == 1
    assert len(plain_logger.handlers) == 1


def test_logger_logging_methods():
    """Test all standard logging methods."""
    logger = get_logger("method_test")

    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_logger_custom_level():
    """Test adding and using custom logging levels."""
    logger = get_logger("custom_test")

    # Add a custom level
    logger.add_level("verbose", 15, {"message": {"color": "blue"}})

    # Should be able to log at custom level
    logger.log("verbose", "This is a verbose message")

    # Check that custom level is registered
    assert "verbose" in logger._custom_levels
    assert logger._custom_levels["verbose"] == 15


def test_logger_level_property():
    """Test logger level property getter and setter."""
    logger = get_logger("level_test", level="warning")
    assert logger.level == "warning"

    logger.level = "debug"
    assert logger.level == "debug"


def test_trace_function_decorator():
    """Test the trace_function decorator."""
    logger = get_logger("trace_test")

    @trace_function(logger=logger, level="info")
    def sample_function(x, y):
        return x + y

    result = sample_function(5, 3)
    assert result == 8


def test_trace_function_with_parameters():
    """Test trace_function decorator with parameter tracking."""
    logger = get_logger("trace_param_test")

    @trace_function(parameters=["x", "y"], logger=logger)
    def add_numbers(x, y, z=10):
        return x + y + z

    result = add_numbers(1, 2)
    assert result == 13


def test_trace_function_exception_handling():
    """Test trace_function decorator handles exceptions properly."""
    logger = get_logger("trace_exception_test")

    @trace_function(logger=logger)
    def failing_function():
        raise ValueError("Test exception")

    with pytest.raises(ValueError, match="Test exception"):
        failing_function()


def test_trace_cls_decorator():
    """Test the trace_cls decorator on a class."""
    logger = get_logger("trace_cls_test")

    @trace_cls(attributes=["value"], logger=logger)
    class TracedClass:
        def __init__(self, initial_value=0):
            self.value = initial_value

        def increment(self):
            self.value += 1

    obj = TracedClass(5)
    assert obj.value == 5

    obj.value = 10
    assert obj.value == 10


def test_trace_cls_with_functions():
    """Test trace_cls decorator with specific function tracing."""
    logger = get_logger("trace_cls_func_test")

    @trace_cls(functions=["increment"], logger=logger)
    class TracedClass:
        def __init__(self):
            self.value = 0

        def increment(self):
            self.value += 1
            return self.value

        def decrement(self):
            self.value -= 1
            return self.value

    obj = TracedClass()
    result = obj.increment()
    assert result == 1

    # This should not be traced
    obj.decrement()
    assert obj.value == 0


def test_universal_trace_decorator_on_function():
    """Test the universal trace decorator on a function."""

    @trace(parameters=["x"])
    def multiply(x, y):
        return x * y

    result = multiply(3, 4)
    assert result == 12


def test_universal_trace_decorator_on_class():
    """Test the universal trace decorator on a class."""

    @trace(attributes=["count"])
    class Counter:
        def __init__(self):
            self.count = 0

        def increment(self):
            self.count += 1

    counter = Counter()
    counter.increment()
    assert counter.count == 1


def test_trace_decorator_without_parameters():
    """Test trace decorator used without parameters."""

    @trace
    def simple_function():
        return "hello"

    result = simple_function()
    assert result == "hello"


def test_logger_display_all_mode():
    """Test logger with display_all=True."""
    logger = get_logger("display_all_test", level="warning", display_all=True)

    # With display_all=True, even debug messages should be logged
    # This is hard to test without capturing output, but we can verify the setup
    assert logger._logger.level <= 10  # DEBUG level or lower


def test_logger_custom_level_styles():
    """Test logger with custom level styles."""
    custom_styles = {"info": {"message": {"color": "green", "bold": True}}}

    logger = get_logger("style_test", levels=custom_styles)

    # Verify the custom style was applied
    assert "info" in logger._level_styles
    assert logger._level_styles["info"]["message"]["color"] == "green"


def test_trace_function_with_rich_styling():
    """Test trace_function with rich styling options."""

    @trace_function(rich=True, style="blue", level="info")
    def styled_function(value):
        return value * 2

    result = styled_function(5)
    assert result == 10


def test_trace_function_without_rich():
    """Test trace_function with rich=False."""

    @trace_function(rich=False, level="info")
    def plain_function(value):
        return value + 1

    result = plain_function(5)
    assert result == 6


def test_logger_name_inference():
    """Test that logger name is inferred from caller when None."""
    logger = get_logger()  # Should infer name from this function
    assert logger.name is not None


def test_logger_underlying_logger_access():
    """Test access to underlying logging.Logger."""
    logger = get_logger("underlying_test")
    underlying = logger.get_logger()

    import logging

    assert isinstance(underlying, logging.Logger)
    assert underlying.name == "underlying_test"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
