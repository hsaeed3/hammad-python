import pytest
from hammad.logging import decorators


class TestTraceFunction:
    """Test cases for the trace_function decorator."""

    def test_trace_function_basic_decoration(self):
        """Test basic function tracing without parameters."""
        call_log = []

        @decorators.trace_function
        def sample_function():
            call_log.append("function_called")
            return "result"

        result = sample_function()
        assert result == "result"
        assert "function_called" in call_log

    def test_trace_function_with_parameters(self):
        """Test function tracing with parameter logging."""

        @decorators.trace_function(parameters=["x", "y"])
        def add_numbers(x, y):
            return x + y

        result = add_numbers(2, 3)
        assert result == 5

    def test_trace_function_with_exception(self):
        """Test function tracing when exception is raised."""

        @decorators.trace_function
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    def test_trace_function_with_custom_logger(self):
        """Test function tracing with custom logger."""
        from hammad.logging import create_logger

        custom_logger = create_logger(name="test_logger", level="debug")

        @decorators.trace_function(logger=custom_logger)
        def logged_function():
            return "success"

        result = logged_function()
        assert result == "success"


class TestTraceClass:
    """Test cases for the trace_cls decorator."""

    def test_trace_cls_basic_decoration(self):
        """Test basic class tracing."""

        @decorators.trace_cls
        class SampleClass:
            def __init__(self, value):
                self.value = value

        instance = SampleClass(42)
        assert instance.value == 42

    def test_trace_cls_with_attributes(self):
        """Test class tracing with attribute monitoring."""

        @decorators.trace_cls(attributes=["value"])
        class TrackedClass:
            def __init__(self, value):
                self.value = value

        instance = TrackedClass(10)
        instance.value = 20
        assert instance.value == 20

    def test_trace_cls_with_functions(self):
        """Test class tracing with function monitoring."""

        @decorators.trace_cls(functions=["calculate"])
        class CalculatorClass:
            def __init__(self, initial=0):
                self.value = initial

            def calculate(self, x, y):
                return x + y

            def untrace_method(self):
                return "not traced"

        calc = CalculatorClass(5)
        result = calc.calculate(3, 4)
        assert result == 7
        assert calc.untrace_method() == "not traced"


class TestTraceUniversal:
    """Test cases for the universal trace decorator."""

    def test_trace_on_function(self):
        """Test universal trace decorator on functions."""

        @decorators.trace
        def simple_function(x):
            return x * 2

        result = simple_function(5)
        assert result == 10

    def test_trace_on_class(self):
        """Test universal trace decorator on classes."""

        @decorators.trace
        class SimpleClass:
            def __init__(self, name):
                self.name = name

        instance = SimpleClass("test")
        assert instance.name == "test"

    def test_trace_with_parameters_on_function(self):
        """Test universal trace decorator with parameters on functions."""

        @decorators.trace(parameters=["a", "b"])
        def multiply(a, b):
            return a * b

        result = multiply(3, 4)
        assert result == 12

    def test_trace_with_attributes_on_class(self):
        """Test universal trace decorator with attributes on classes."""

        @decorators.trace(attributes=["counter"])
        class CounterClass:
            def __init__(self):
                self.counter = 0

            def increment(self):
                self.counter += 1

        counter = CounterClass()
        counter.increment()
        assert counter.counter == 1

    def test_trace_with_custom_settings(self):
        """Test universal trace decorator with custom settings."""

        @decorators.trace(level="info", rich=False, style="green")
        def styled_function():
            return "styled"

        result = styled_function()
        assert result == "styled"

    def test_trace_decorator_preserves_function_metadata(self):
        """Test that trace decorator preserves function metadata."""

        @decorators.trace
        def documented_function():
            """This is a documented function."""
            return "documented"

        assert documented_function.__doc__ == "This is a documented function."
        assert documented_function.__name__ == "documented_function"


class TestDecoratorEdgeCases:
    """Test edge cases and error conditions for decorators."""

    def test_trace_function_with_no_return(self):
        """Test tracing function that returns None."""

        @decorators.trace_function
        def void_function():
            pass

        result = void_function()
        assert result is None

    def test_trace_function_with_complex_parameters(self):
        """Test tracing function with complex parameter types."""

        @decorators.trace_function(parameters=["data"])
        def process_data(data):
            return len(data)

        result = process_data({"key": "value", "list": [1, 2, 3]})
        assert result == 2

    def test_trace_cls_with_inheritance(self):
        """Test class tracing with inheritance."""

        @decorators.trace_cls(attributes=["base_value"])
        class BaseClass:
            def __init__(self, value):
                self.base_value = value

        class DerivedClass(BaseClass):
            def __init__(self, value, extra):
                super().__init__(value)
                self.extra = extra

        instance = DerivedClass(10, "extra")
        assert instance.base_value == 10
        assert instance.extra == "extra"

    def test_decorator_with_different_level_types(self):
        """Test decorators with different level type specifications."""

        # Test with string level
        @decorators.trace(level="warning")
        def string_level_func():
            return "warning_level"

        # Test with int level (logging.WARNING = 30)
        @decorators.trace(level=30)
        def int_level_func():
            return "int_level"

        assert string_level_func() == "warning_level"
        assert int_level_func() == "int_level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
