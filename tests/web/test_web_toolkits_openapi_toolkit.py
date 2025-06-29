import pytest
from hammad.web.openapi.client import (
    AsyncOpenAPIClient as OpenApiToolkit,
    OpenAPIError as OpenApiToolkitError,
    OpenAPIOperation as OpenApiOperation,
    ParameterInfo,
    RequestBodyInfo,
    ResponseInfo,
    OpenAPISpec as OpenApiSpec,
)

import json
from unittest.mock import AsyncMock, patch
from typing import Dict, Any
import httpx


# Sample OpenAPI specification for testing
SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "servers": [{"url": "https://api.example.com"}],
    "paths": {
        "/users": {
            "get": {
                "operationId": "getUsers",
                "summary": "Get all users",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 10},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"type": "object"}}
                            }
                        },
                    }
                },
            },
            "post": {
                "operationId": "createUser",
                "summary": "Create a user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"},
                                },
                                "required": ["name", "email"],
                            }
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            },
        },
        "/users/{id}": {
            "get": {
                "operationId": "getUserById",
                "summary": "Get user by ID",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "404": {"description": "Not found"},
                },
            }
        },
    },
}


# Mock server responses for testing
class MockResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        text: str = "",
        headers: Dict[str, str] = None,
        url: str = "https://api.example.com/test",
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or json.dumps(self._json_data)
        self.headers = headers or {"content-type": "application/json"}
        self.url = url
        self.request = AsyncMock()
        self.request.method = "GET"

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not self.is_success:
            raise httpx.HTTPStatusError(
                message=f"HTTP {self.status_code}", request=self.request, response=self
            )


@pytest.mark.asyncio
async def test_openapi_toolkit_init():
    """Test OpenApiToolkit initialization."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)
    assert toolkit.spec.openapi == "3.0.0"
    assert toolkit.spec.info["title"] == "Test API"
    assert toolkit.base_url == "https://api.example.com"
    assert len(toolkit.spec.operations) == 3


@pytest.mark.asyncio
async def test_openapi_toolkit_init_with_base_url_override():
    """Test OpenApiToolkit initialization with base URL override."""
    custom_base_url = "https://custom.example.com"
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC, base_url=custom_base_url)
    assert toolkit.base_url == custom_base_url


@pytest.mark.asyncio
async def test_openapi_toolkit_init_invalid_spec():
    """Test OpenApiToolkit initialization with invalid spec."""
    with pytest.raises(OpenApiToolkitError) as exc_info:
        OpenApiToolkit({})
    assert "OpenAPI version not specified" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openapi_toolkit_init_missing_info():
    """Test OpenApiToolkit initialization with missing info."""
    invalid_spec = {"openapi": "3.0.0"}
    with pytest.raises(OpenApiToolkitError) as exc_info:
        OpenApiToolkit(invalid_spec)
    assert "OpenAPI info section missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_parse_json_spec():
    """Test parsing JSON OpenAPI specification."""
    json_spec = json.dumps(SAMPLE_OPENAPI_SPEC)
    toolkit = OpenApiToolkit(json_spec)
    assert toolkit.spec.openapi == "3.0.0"


@pytest.mark.asyncio
async def test_parse_yaml_spec():
    """Test parsing YAML OpenAPI specification."""
    yaml_spec = """
openapi: "3.0.0"
info:
  title: "Test API"
  version: "1.0.0"
servers:
  - url: "https://api.example.com"
paths:
  /test:
    get:
      operationId: testGet
      responses:
        "200":
          description: Success
"""
    toolkit = OpenApiToolkit(yaml_spec)
    assert toolkit.spec.openapi == "3.0.0"
    assert toolkit.spec.info["title"] == "Test API"


@pytest.mark.asyncio
async def test_get_operations():
    """Test getting all operations."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)
    operations = toolkit.get_operations()
    assert len(operations) == 3
    operation_ids = [op.operation_id for op in operations]
    assert "getUsers" in operation_ids
    assert "createUser" in operation_ids
    assert "getUserById" in operation_ids


@pytest.mark.asyncio
async def test_get_operation_by_id():
    """Test getting operation by ID."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    # Test existing operation
    operation = toolkit.get_operation("getUsers")
    assert operation is not None
    assert operation.operation_id == "getUsers"
    assert operation.method == "GET"
    assert operation.path == "/users"

    # Test non-existing operation
    operation = toolkit.get_operation("nonExistentOperation")
    assert operation is None


@pytest.mark.asyncio
async def test_get_operations_by_tag():
    """Test getting operations by tag."""
    spec_with_tags = SAMPLE_OPENAPI_SPEC.copy()
    spec_with_tags["paths"]["/users"]["get"]["tags"] = ["users"]
    spec_with_tags["paths"]["/users"]["post"]["tags"] = ["users"]
    spec_with_tags["paths"]["/users/{id}"]["get"]["tags"] = ["users", "individual"]

    toolkit = OpenApiToolkit(spec_with_tags)

    # Test operations by tag
    user_ops = toolkit.get_operations_by_tag("users")
    assert len(user_ops) == 3

    individual_ops = toolkit.get_operations_by_tag("individual")
    assert len(individual_ops) == 1
    assert individual_ops[0].operation_id == "getUserById"


@pytest.mark.asyncio
async def test_find_operations():
    """Test finding operations by path and method."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    # Test by path
    user_ops = toolkit.find_operations(path="/users")
    assert len(user_ops) == 3  # All operations contain "/users"

    # Test by method
    get_ops = toolkit.find_operations(method="GET")
    assert len(get_ops) == 2

    # Test by path and method
    get_user_ops = toolkit.find_operations(path="/users", method="GET")
    assert len(get_user_ops) == 2


@pytest.mark.asyncio
async def test_successful_execute_operation():
    """Test successful operation execution."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    mock_response = MockResponse(
        status_code=200,
        json_data=[{"id": 1, "name": "Test User"}],
        headers={"content-type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await toolkit.execute_operation("getUsers", parameters={"limit": 5})

        assert response.status_code == 200
        assert response.json_data == [{"id": 1, "name": "Test User"}]


@pytest.mark.asyncio
async def test_execute_operation_with_path_params():
    """Test operation execution with path parameters."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    mock_response = MockResponse(
        status_code=200,
        json_data={"id": 123, "name": "Test User"},
        headers={"content-type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await toolkit.execute_operation(
            "getUserById", parameters={"id": 123}
        )

        assert response.status_code == 200
        # Verify the URL was built correctly with path parameter
        mock_client.return_value.__aenter__.return_value.request.assert_called_once()


@pytest.mark.asyncio
async def test_execute_operation_with_request_body():
    """Test operation execution with request body."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    mock_response = MockResponse(
        status_code=201,
        json_data={"id": 1, "name": "New User", "email": "new@example.com"},
        headers={"content-type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await toolkit.execute_operation(
            "createUser", request_body={"name": "New User", "email": "new@example.com"}
        )

        assert response.status_code == 201
        assert response.json_data["name"] == "New User"


@pytest.mark.asyncio
async def test_execute_operation_missing_required_param():
    """Test operation execution with missing required parameter."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    with pytest.raises(OpenApiToolkitError) as exc_info:
        await toolkit.execute_operation(
            "getUserById"
        )  # Missing required "id" parameter

    error = exc_info.value
    assert "Required parameter 'id' not provided" in str(error)
    assert error.operation_id == "getUserById"


@pytest.mark.asyncio
async def test_execute_operation_unresolved_path_params():
    """Test operation execution with unresolved path parameters."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    mock_response = MockResponse(status_code=200)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(OpenApiToolkitError) as exc_info:
            await toolkit.execute_operation(
                "getUserById",
                parameters={"wrong_param": 123},  # Not providing "id"
            )

    error = exc_info.value
    assert "Required parameter 'id' not provided" in str(error)
    assert "id" in str(error)


@pytest.mark.asyncio
async def test_execute_operation_not_found():
    """Test operation execution with non-existent operation."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    with pytest.raises(OpenApiToolkitError) as exc_info:
        await toolkit.execute_operation("nonExistentOperation")

    error = exc_info.value
    assert "Operation 'nonExistentOperation' not found" in str(error)
    assert "available operations" in str(error)


@pytest.mark.asyncio
async def test_generate_example_request():
    """Test generating example requests."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    # Test operation with parameters
    example = toolkit.generate_example_request("getUsers")
    assert "parameters" in example
    assert "limit" in example["parameters"]
    assert example["request_body"] is None

    # Test operation with request body
    example = toolkit.generate_example_request("createUser")
    assert "request_body" in example
    assert example["request_body"] is not None
    assert "name" in example["request_body"]
    assert "email" in example["request_body"]


@pytest.mark.asyncio
async def test_generate_example_request_not_found():
    """Test generating example request for non-existent operation."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    with pytest.raises(OpenApiToolkitError) as exc_info:
        toolkit.generate_example_request("nonExistentOperation")

    error = exc_info.value
    assert "Operation 'nonExistentOperation' not found" in str(error)


@pytest.mark.asyncio
async def test_generate_example_value():
    """Test example value generation for different schema types."""
    toolkit = OpenApiToolkit(SAMPLE_OPENAPI_SPEC)

    # Test string
    assert toolkit._generate_example_value({"type": "string"}) == "example_string"

    # Test string with format
    assert (
        toolkit._generate_example_value({"type": "string", "format": "email"})
        == "user@example.com"
    )
    assert (
        toolkit._generate_example_value({"type": "string", "format": "date"})
        == "2024-01-01"
    )

    # Test integer
    assert toolkit._generate_example_value({"type": "integer"}) == 42

    # Test number
    assert toolkit._generate_example_value({"type": "number"}) == 3.14

    # Test boolean
    assert toolkit._generate_example_value({"type": "boolean"}) is True

    # Test array
    array_example = toolkit._generate_example_value(
        {"type": "array", "items": {"type": "string"}}
    )
    assert isinstance(array_example, list)
    assert len(array_example) == 1

    # Test object
    object_example = toolkit._generate_example_value(
        {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"],
        }
    )
    assert isinstance(object_example, dict)
    assert "name" in object_example

    # Test enum
    assert (
        toolkit._generate_example_value(
            {"type": "string", "enum": ["option1", "option2"]}
        )
        == "option1"
    )

    # Test with example
    assert (
        toolkit._generate_example_value({"type": "string", "example": "custom_example"})
        == "custom_example"
    )


@pytest.mark.asyncio
async def test_openapi_toolkit_error():
    """Test OpenApiToolkitError functionality."""
    error = OpenApiToolkitError(
        message="Test error",
        suggestion="Test suggestion",
        context={"key": "value"},
        schema_path="/users",
        operation_id="getUsers",
    )

    full_error = error.get_full_error()
    assert "OPENAPI ERROR: Test error" in full_error
    assert "Operation: getUsers" in full_error
    assert "Path: /users" in full_error
    assert "SUGGESTION: Test suggestion" in full_error
    assert "CONTEXT: {'key': 'value'}" in full_error


@pytest.mark.asyncio
async def test_parameter_info_model():
    """Test ParameterInfo model."""
    param = ParameterInfo(
        name="test_param",
        location="query",
        required=True,
        schema={"type": "string"},
        description="Test parameter",
    )

    assert param.name == "test_param"
    assert param.location == "query"
    assert param.required is True
    assert param.schema_ == {"type": "string"}
    assert param.description == "Test parameter"


@pytest.mark.asyncio
async def test_request_body_info_model():
    """Test RequestBodyInfo model."""
    request_body = RequestBodyInfo(
        required=True,
        content_schema={"application/json": {"type": "object"}},
        description="Test request body",
    )

    assert request_body.required is True
    assert "application/json" in request_body.content_schema
    assert request_body.description == "Test request body"


@pytest.mark.asyncio
async def test_response_info_model():
    """Test ResponseInfo model."""
    response = ResponseInfo(
        description="Success response",
        content_schema={"application/json": {"type": "object"}},
    )

    assert response.description == "Success response"
    assert "application/json" in response.content_schema


@pytest.mark.asyncio
async def test_openapi_operation_model():
    """Test OpenApiOperation model."""
    operation = OpenApiOperation(
        path="/test",
        method="post",  # Should be uppercased
        operation_id="testOperation",
        summary="Test operation",
        description="Test description",
        tags=["test"],
        parameters=[],
        request_body=None,
        responses={},
    )

    assert operation.path == "/test"
    assert operation.method == "POST"  # Should be uppercased
    assert operation.operation_id == "testOperation"
    assert operation.summary == "Test operation"


@pytest.mark.asyncio
async def test_openapi_spec_model():
    """Test OpenApiSpec model."""
    spec = OpenApiSpec(
        openapi="3.0.0",
        info={"title": "Test", "version": "1.0.0"},
        servers=[{"url": "https://api.example.com"}],
        operations=[],
        components={},
    )

    assert spec.openapi == "3.0.0"
    assert spec.info["title"] == "Test"
    assert spec.base_url == "https://api.example.com"


@pytest.mark.asyncio
async def test_openapi_spec_no_servers():
    """Test OpenApiSpec with no servers."""
    spec = OpenApiSpec(
        openapi="3.0.0", info={"title": "Test", "version": "1.0.0"}, operations=[]
    )

    assert spec.base_url is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
