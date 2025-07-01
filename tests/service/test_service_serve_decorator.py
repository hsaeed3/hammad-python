import pytest
from hammad.service.decorators import serve


class TestServeDecorator:
    """Test cases for the @serve decorator functionality."""

    def test_serve_decorator_with_parentheses(self):
        """Test @serve(...) decorator with parameters."""

        @serve(name="test_service", port=8001, auto_start=False)
        def test_function(x: int, y: str = "default") -> str:
            return f"Result: {x}, {y}"

        # Check that the function has service configuration stored
        assert hasattr(test_function, "_service_config")
        config = test_function._service_config
        assert config["name"] == "test_service"
        assert config["port"] == 8001
        assert config["auto_start"] is False
        assert config["method"] == "POST"  # default
        assert config["path"] == "/"  # default

    def test_serve_decorator_without_parentheses(self):
        """Test @serve decorator without parentheses."""

        @serve
        def test_function(x: int) -> int:
            return x * 2

        # Check that the function has service configuration with defaults
        assert hasattr(test_function, "_service_config")
        config = test_function._service_config
        assert config["name"] == "test_function"  # defaults to function name
        assert config["port"] == 8000  # default
        assert config["method"] == "POST"  # default
        assert config["auto_start"] is True  # default

    def test_serve_as_function_call(self):
        """Test serve() called as a function."""

        def original_function(data: str) -> str:
            return f"Processed: {data}"

        # Call serve as a function
        decorated_function = serve(
            original_function, name="custom_service", method="GET"
        )

        # Should return the same function
        assert decorated_function is original_function
        assert hasattr(decorated_function, "_service_config")
        config = decorated_function._service_config
        assert config["name"] == "custom_service"
        assert config["method"] == "GET"

    def test_serve_with_custom_parameters(self):
        """Test serve decorator with various custom parameters."""

        @serve(
            name="advanced_service",
            method="PUT",
            path="/api/data",
            host="127.0.0.1",
            port=9000,
            log_level="debug",
            reload=True,
            workers=2,
            auto_start=False,
            include_in_schema=False,
            tags=["test", "api"],
            description="Test service description",
        )
        def advanced_function(item_id: int, data: dict) -> dict:
            return {"id": item_id, "data": data}

        config = advanced_function._service_config
        assert config["name"] == "advanced_service"
        assert config["method"] == "PUT"
        assert config["path"] == "/api/data"
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 9000
        assert config["log_level"] == "debug"
        assert config["reload"] is True
        assert config["workers"] == 2
        assert config["auto_start"] is False
        assert config["include_in_schema"] is False
        assert config["tags"] == ["test", "api"]
        assert config["description"] == "Test service description"

    def test_serve_with_dependencies(self):
        """Test serve decorator with dependencies."""

        def mock_dependency():
            pass

        @serve(dependencies=[mock_dependency], auto_start=False)
        def function_with_deps(x: int) -> int:
            return x + 1

        config = function_with_deps._service_config
        assert config["dependencies"] == [mock_dependency]

    def test_serve_http_methods(self):
        """Test serve decorator with different HTTP methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]

        for method in methods:

            @serve(method=method, auto_start=False)
            def test_method_function(data: str) -> str:
                return data

            config = test_method_function._service_config
            assert config["method"] == method

    def test_serve_preserves_function_metadata(self):
        """Test that the serve decorator preserves function metadata."""

        @serve(auto_start=False)
        def documented_function(x: int, y: str = "test") -> str:
            """This function has documentation.

            Args:
                x: An integer parameter
                y: A string parameter with default

            Returns:
                A formatted string
            """
            return f"{x}: {y}"

        # Function should retain its original attributes
        assert documented_function.__name__ == "documented_function"
        assert "This function has documentation" in documented_function.__doc__

        # But should also have service config
        assert hasattr(documented_function, "_service_config")

    def test_serve_with_none_values(self):
        """Test serve decorator with None values for optional parameters."""

        @serve(
            name=None,  # Should default to function name
            dependencies=None,
            tags=None,
            description=None,
            auto_start=False,
        )
        def function_with_nones(x: int) -> int:
            return x

        config = function_with_nones._service_config
        assert config["name"] == "function_with_nones"  # Should use function name
        assert config["dependencies"] is None
        assert config["tags"] is None
        assert config["description"] is None

    def test_serve_function_callable_after_decoration(self):
        """Test that the decorated function is still callable."""

        @serve(auto_start=False)
        def callable_function(x: int, y: int = 10) -> int:
            return x + y

        # Function should still be callable with original behavior
        result = callable_function(5)
        assert result == 15

        result = callable_function(3, 7)
        assert result == 10


if __name__ == "__main__":
    pytest.main([__file__, "-vs"])
