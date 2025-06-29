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


class TestTraceHttp:
    """Test cases for the trace_http decorator."""

    def test_trace_http_basic_decoration(self):
        """Test basic HTTP tracing without parameters."""

        @decorators.trace_http
        def mock_http_request():
            # Mock response object
            class MockResponse:
                def __init__(self):
                    self.status_code = 200
                    self.text = '{"success": true}'
                    self.headers = {"Content-Type": "application/json"}

            return MockResponse()

        result = mock_http_request()
        assert result.status_code == 200

    def test_trace_http_with_request_params(self):
        """Test HTTP tracing with request parameters."""

        @decorators.trace_http
        def api_call(url, method="GET", headers=None, data=None):
            class MockResponse:
                def __init__(self):
                    self.status_code = 201
                    self.text = '{"created": true}'
                    self.headers = {"Content-Type": "application/json"}

            return MockResponse()

        result = api_call(
            url="https://api.example.com/users",
            method="POST",
            headers={"Authorization": "Bearer token"},
            data={"name": "test"},
        )
        assert result.status_code == 201

    def test_trace_http_with_exception(self):
        """Test HTTP tracing when exception is raised."""

        @decorators.trace_http
        def failing_request(url):
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError, match="Network error"):
            failing_request("https://api.example.com")

    def test_trace_http_show_request_only(self):
        """Test HTTP tracing with only request logging enabled."""

        @decorators.trace_http(show_request=True, show_response=False)
        def request_only(endpoint, params=None):
            return {"data": "response"}

        result = request_only("https://api.test.com", params={"q": "search"})
        assert result == {"data": "response"}

    def test_trace_http_show_response_only(self):
        """Test HTTP tracing with only response logging enabled."""

        @decorators.trace_http(show_request=False, show_response=True)
        def response_only():
            return {"status": "ok", "data": [1, 2, 3]}

        result = response_only()
        assert result["status"] == "ok"

    def test_trace_http_with_custom_logger(self):
        """Test HTTP tracing with custom logger."""
        from hammad.logging import create_logger

        custom_logger = create_logger(name="http_test", level="info")

        @decorators.trace_http(logger=custom_logger)
        def logged_request(uri):
            class MockResponse:
                def __init__(self):
                    self.status_code = 200
                    self.content = b'{"result": "success"}'

            return MockResponse()

        result = logged_request("https://example.com/api")
        assert result.status_code == 200

    def test_trace_http_with_dict_response(self):
        """Test HTTP tracing with dictionary response."""

        @decorators.trace_http
        def dict_response():
            return {"message": "success", "code": 200, "data": {"id": 123}}

        result = dict_response()
        assert result["code"] == 200

    def test_trace_http_with_string_response(self):
        """Test HTTP tracing with string response."""

        @decorators.trace_http
        def string_response():
            return "Plain text response"

        result = string_response()
        assert result == "Plain text response"

    def test_trace_http_with_none_response(self):
        """Test HTTP tracing with None response."""

        @decorators.trace_http
        def none_response():
            return None

        result = none_response()
        assert result is None

    def test_trace_http_decorator_preserves_metadata(self):
        """Test that trace_http decorator preserves function metadata."""

        @decorators.trace_http
        def documented_http_function():
            """Makes an HTTP request and returns response."""
            return {"documented": True}

        assert (
            documented_http_function.__doc__
            == "Makes an HTTP request and returns response."
        )
        assert documented_http_function.__name__ == "documented_http_function"

    def test_trace_http_direct_result_call(self):
        """Test trace_http with direct result (already executed function)."""

        # Simulate a function result
        mock_result = {"message": "Hello", "status": "success"}

        # This should just log the response and return the result
        result = decorators.trace_http(
            mock_result, show_request=False, show_response=True
        )

        assert result == mock_result

    def test_trace_http_wrapped_function_call(self):
        """Test trace_http wrapping a function directly."""

        def api_function(endpoint, method="GET"):
            return {"url": endpoint, "method": method, "status": 200}

        # Wrap the function
        traced_api = decorators.trace_http(
            api_function, show_request=True, show_response=True
        )

        # Call the wrapped function
        result = traced_api("https://api.example.com", method="POST")

        assert result["status"] == 200
        assert result["method"] == "POST"

    @pytest.mark.asyncio
    async def test_trace_http_async_function(self):
        """Test trace_http with async functions."""

        @decorators.trace_http
        async def async_api_call(url):
            # Simulate async API call
            class MockAsyncResponse:
                def __init__(self):
                    self.status_code = 200
                    self.text = '{"async": true}'

            return MockAsyncResponse()

        result = await async_api_call("https://async-api.com")
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_trace_http_async_wrapped_function(self):
        """Test trace_http wrapping an async function directly."""

        async def async_function(data):
            return {"processed": data, "async": True}

        # Wrap the async function
        traced_async = decorators.trace_http(async_function)

        # Call the wrapped async function
        result = await traced_async({"test": "data"})

        assert result["async"] is True
        assert result["processed"]["test"] == "data"

    def test_trace_http_llm_response_format(self):
        """Test trace_http with LLM-style response objects."""

        class MockLLMResponse:
            def __init__(self):
                self.choices = [MockChoice()]

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        class MockMessage:
            def __init__(self):
                self.content = "This is a test response from an LLM"

        mock_llm_result = MockLLMResponse()

        # Test direct result logging
        result = decorators.trace_http(mock_llm_result, show_response=True)

        assert (
            result.choices[0].message.content == "This is a test response from an LLM"
        )

    def test_trace_http_request_exclude_none(self):
        """Test trace_http with request_exclude_none parameter."""

        @decorators.trace_http(request_exclude_none=True)
        def function_with_none_params(param1, param2=None, param3=None):
            return {"param1": param1, "filtered": "params"}

        result = function_with_none_params("value")
        assert result["param1"] == "value"

    def test_trace_http_response_exclude_none(self):
        """Test trace_http with response_exclude_none parameter."""

        @decorators.trace_http(response_exclude_none=True)
        def function_returning_none():
            return None

        # This should not log the response since it's None and exclude_none=True
        result = function_returning_none()
        assert result is None

    def test_trace_http_both_exclude_none(self):
        """Test trace_http with both exclude_none parameters."""

        @decorators.trace_http(request_exclude_none=True, response_exclude_none=True)
        def test_function(param1, param2=None):
            if param2 is None:
                return None
            return {"result": param1}

        # Test with None parameter and None return
        result1 = test_function("test")
        assert result1 is None

        # Test with non-None parameter and non-None return
        result2 = test_function("test", "value")
        assert result2["result"] == "test"


class TestInstallTraceHttp:
    """Test cases for the install_trace_http function."""

    def test_install_trace_http_no_modules(self):
        """Test install_trace_http when no HTTP modules are loaded."""
        import sys

        # Store original modules
        original_modules = sys.modules.copy()

        # Remove HTTP modules temporarily
        modules_to_remove = [
            "requests",
            "httpx",
            "aiohttp",
            "litellm",
            "openai",
            "anthropic",
        ]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]

        try:
            # This should not crash and should show warning
            decorators.install_trace_http()

        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_install_trace_http_basic_functionality(self):
        """Test basic install_trace_http functionality."""

        # This test just ensures the function can be called without error
        # when HTTP libraries are available
        decorators.install_trace_http(
            show_request=True,
            show_response=True,
            request_exclude_none=True,
            response_exclude_none=False,
        )


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
