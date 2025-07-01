import pytest
from hammad.service.decorators import serve_mcp


class TestServeMCPDecorator:
    """Test cases for the @serve_mcp decorator functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Import here to avoid side effects during import
        from hammad.mcp.servers.launcher import shutdown_all_servers

        yield

        # Clean up any running servers after each test
        try:
            shutdown_all_servers(force_kill_timeout=1.0)
        except Exception:
            pass  # Ignore cleanup errors

    def test_serve_mcp_decorator_with_parentheses(self):
        """Test @serve_mcp(...) decorator with parameters."""

        @serve_mcp(name="test_mcp_service", transport="stdio")
        def test_function(x: int, y: str = "default") -> str:
            """Test function for MCP server."""
            return f"Result: {x}, {y}"

        # The original function should be returned unchanged
        assert callable(test_function)
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function for MCP server."

    def test_serve_mcp_decorator_without_parentheses(self):
        """Test @serve_mcp decorator without parentheses."""

        @serve_mcp
        def test_function(x: int) -> int:
            """Another test function."""
            return x * 2

        # The original function should be returned unchanged
        assert callable(test_function)
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Another test function."

    def test_serve_mcp_with_single_function(self):
        """Test serve_mcp called with a single function."""

        def test_function(data: str) -> str:
            """Process some data."""
            return f"Processed: {data}"

        result = serve_mcp(test_function, name="single_func_server")

        # Should return the original function
        assert result is test_function
        assert result.__name__ == "test_function"

    def test_serve_mcp_with_multiple_functions(self):
        """Test serve_mcp called with multiple functions."""

        def func1(x: int) -> int:
            """Function 1."""
            return x + 1

        def func2(y: str) -> str:
            """Function 2."""
            return y.upper()

        functions = [func1, func2]
        result = serve_mcp(functions, name="multi_func_server")

        # Should return the original list
        assert result == functions
        assert len(result) == 2

    def test_serve_mcp_with_sse_transport(self):
        """Test serve_mcp with SSE transport configuration."""

        @serve_mcp(
            name="sse_server",
            transport="sse",
            host="localhost",
            port=8001,
            sse_path="/events",
        )
        def sse_function(message: str) -> str:
            """SSE test function."""
            return f"SSE: {message}"

        assert callable(sse_function)
        assert sse_function.__name__ == "sse_function"

    def test_serve_mcp_with_streamable_http_transport(self):
        """Test serve_mcp with StreamableHTTP transport configuration."""

        @serve_mcp(
            name="http_server",
            transport="streamable-http",
            host="127.0.0.1",
            port=8002,
            streamable_http_path="/stream",
        )
        def http_function(data: dict) -> dict:
            """HTTP test function."""
            return {"response": data}

        assert callable(http_function)
        assert http_function.__name__ == "http_function"

    def test_serve_mcp_with_custom_instructions(self):
        """Test serve_mcp with custom instructions."""

        @serve_mcp(
            name="custom_server",
            instructions="This is a custom MCP server for testing",
            single_func_description="Custom function description",
        )
        def custom_function(value: float) -> float:
            """Custom test function."""
            return value * 2.5

        assert callable(custom_function)
        assert custom_function.__name__ == "custom_function"

    def test_serve_mcp_with_debug_settings(self):
        """Test serve_mcp with debug and logging settings."""

        @serve_mcp(
            name="debug_server",
            log_level="DEBUG",
            debug_mode=True,
            auto_restart=True,
            check_interval=2.0,
        )
        def debug_function(debug_data: str) -> str:
            """Debug test function."""
            return f"Debug: {debug_data}"

        assert callable(debug_function)
        assert debug_function.__name__ == "debug_function"

    def test_serve_mcp_with_invalid_transport(self):
        """Test serve_mcp with invalid transport raises error."""
        with pytest.raises(ValueError, match="Unsupported transport"):

            @serve_mcp(transport="invalid_transport")
            def invalid_function():
                pass

    def test_serve_mcp_with_invalid_input_type(self):
        """Test serve_mcp with invalid input type raises error."""
        with pytest.raises(TypeError, match="Expected callable or list of callables"):
            serve_mcp("not_a_function")

    def test_serve_mcp_function_execution_after_decoration(self):
        """Test that decorated functions can still be called normally."""

        @serve_mcp(name="execution_test")
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Function should still work normally
        result = add_numbers(5, 3)
        assert result == 8

    def test_serve_mcp_preserves_function_metadata(self):
        """Test that serve_mcp preserves function metadata."""

        def original_function(x: int, y: str = "test") -> str:
            """Original function docstring."""
            return f"{x}: {y}"

        decorated = serve_mcp(original_function, name="metadata_test")

        # Metadata should be preserved
        assert decorated.__name__ == original_function.__name__
        assert decorated.__doc__ == original_function.__doc__
        assert decorated.__annotations__ == original_function.__annotations__

    def test_serve_mcp_empty_function_list(self):
        """Test serve_mcp with empty function list."""
        result = serve_mcp([], name="empty_server")
        assert result == []

    def test_serve_mcp_default_server_name_for_multiple_functions(self):
        """Test default server name generation for multiple functions."""

        def func1():
            pass

        def func2():
            pass

        result = serve_mcp([func1, func2])
        # Should not raise an error and return the functions
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-vs"])
