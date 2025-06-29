"""hammad.web.openapi.client"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Literal, Optional, Union, overload

from msgspec import yaml
from pydantic import BaseModel, Field, field_validator

from ..http.client import AsyncHttpClient, HttpRequest, HttpResponse, HttpError

__all__ = (
    "OpenAPIError",
    "ParameterInfo",
    "RequestBodyInfo",
    "ResponseInfo",
    "OpenAPIOperation",
    "OpenAPISpec",
    "OpenAPIClient",
    "AsyncOpenAPIClient",
    "create_openapi_client",
)


class OpenAPIError(HttpError):
    """Custom exception for OpenAPI toolkit errors with semantic feedback."""

    def __init__(
        self,
        message: str,
        suggestion: str = "",
        context: Optional[Dict[str, Any]] = None,
        schema_path: Optional[str] = None,
        operation_id: Optional[str] = None,
    ):
        super().__init__(message, suggestion, context)
        self.schema_path = schema_path
        self.operation_id = operation_id

    def get_full_error(self) -> str:
        """Get the full error message with OpenAPI-specific context."""
        error_msg = f"OPENAPI ERROR: {self.message}"
        if self.operation_id:
            error_msg += f" (Operation: {self.operation_id})"
        if self.schema_path:
            error_msg += f" (Path: {self.schema_path})"
        if self.suggestion:
            error_msg += f"\nSUGGESTION: {self.suggestion}"
        if self.context:
            error_msg += f"\nCONTEXT: {self.context}"
        return error_msg

    def __str__(self) -> str:
        """Return the full error message when converting to string."""
        return self.get_full_error()


class ParameterInfo(BaseModel):
    """Represents a single parameter for an HTTP operation."""

    name: str
    location: Literal["path", "query", "header", "cookie"]
    required: bool = False
    schema_: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    description: Optional[str] = None


class RequestBodyInfo(BaseModel):
    """Represents the request body for an HTTP operation."""

    required: bool = False
    content_schema: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict
    )  # Key: media type
    description: Optional[str] = None


class ResponseInfo(BaseModel):
    """Represents response information."""

    description: Optional[str] = None
    content_schema: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict
    )  # Key: media type


class OpenAPIOperation(BaseModel):
    """Represents a single OpenAPI operation."""

    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    parameters: List[ParameterInfo] = Field(default_factory=list)
    request_body: Optional[RequestBodyInfo] = None
    responses: Dict[str, ResponseInfo] = Field(default_factory=dict)

    @field_validator("method", mode="before")
    @classmethod
    def validate_method(cls, v):
        """Validate HTTP method."""
        return v.upper()


class OpenAPISpec(BaseModel):
    """Represents a parsed OpenAPI specification."""

    openapi: str
    info: Dict[str, Any]
    servers: List[Dict[str, Any]] = Field(default_factory=list)
    operations: List[OpenAPIOperation] = Field(default_factory=list)
    components: Dict[str, Any] = Field(default_factory=dict)

    @property
    def base_url(self) -> Optional[str]:
        """Get the base URL from servers."""
        if self.servers:
            return self.servers[0].get("url")
        return None


class AsyncOpenAPIClient(AsyncHttpClient):
    """
    OpenAPI toolkit that extends HttpToolkit with OpenAPI schema parsing and operation execution.

    This class parses OpenAPI specifications and provides methods to execute operations
    with proper parameter validation and semantic error handling.
    """

    def __init__(
        self,
        openapi_spec: Union[str, Dict[str, Any]],
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        # Semantic authentication parameters
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
        bearer_token: Optional[str] = None,
        basic_auth: Optional[tuple[str, str]] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the OpenAPI toolkit.

        Args:
            openapi_spec: OpenAPI specification as dict, JSON string, or YAML string
            base_url: Base URL override (uses spec servers if not provided)
            default_headers: Default headers to include in all requests
            timeout: Default timeout in seconds
            follow_redirects: Whether to follow redirects by default
            verify_ssl: Whether to verify SSL certificates
            api_key: API key for authentication
            api_key_header: Header name for API key (default: X-API-Key)
            bearer_token: Bearer token for Authorization header
            basic_auth: Tuple of (username, password) for basic auth
            user_agent: User-Agent header value
        """
        # Parse the OpenAPI spec
        self.spec = self._parse_openapi_spec(openapi_spec)

        # Use base_url override or get from spec
        resolved_base_url = base_url or self.spec.base_url

        # Initialize the parent HttpToolkit
        super().__init__(
            base_url=resolved_base_url,
            default_headers=default_headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
            basic_auth=basic_auth,
            user_agent=user_agent,
        )

    def _parse_openapi_spec(self, spec: Union[str, Dict[str, Any]]) -> OpenAPISpec:
        """Parse OpenAPI specification from various formats."""
        try:
            # Handle different input types
            if isinstance(spec, str):
                # Try to parse as JSON first
                try:
                    spec_dict = json.loads(spec)
                except json.JSONDecodeError:
                    # Try to parse as YAML
                    try:
                        spec_dict = yaml.decode(
                            spec.encode() if isinstance(spec, str) else spec
                        )
                    except Exception as e:
                        raise OpenAPIError(
                            message="Failed to parse OpenAPI specification",
                            suggestion="Ensure the specification is valid JSON or YAML",
                            context={"parsing_error": str(e)},
                        )
            elif isinstance(spec, dict):
                spec_dict = spec
            else:
                raise OpenAPIError(
                    message="Invalid OpenAPI specification format",
                    suggestion="Provide specification as dict, JSON string, or YAML string",
                    context={"provided_type": type(spec).__name__},
                )

            # Validate required fields
            if "openapi" not in spec_dict:
                raise OpenAPIError(
                    message="OpenAPI version not specified",
                    suggestion="Include 'openapi' field with version (e.g., '3.0.0')",
                    context={"spec_keys": list(spec_dict.keys())},
                )

            if "info" not in spec_dict:
                raise OpenAPIError(
                    message="OpenAPI info section missing",
                    suggestion="Include 'info' section with title and version",
                    context={"spec_keys": list(spec_dict.keys())},
                )

            # Parse operations from paths
            operations = []
            paths = spec_dict.get("paths", {})

            for path_str, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue

                # Extract operations for each HTTP method
                for method in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                ]:
                    operation_data = path_item.get(method)
                    if not operation_data:
                        continue

                    try:
                        operation = self._parse_operation(
                            path_str, method, operation_data
                        )
                        operations.append(operation)
                    except Exception as e:
                        # Log the error but continue processing other operations
                        print(
                            f"Warning: Failed to parse operation {method.upper()} {path_str}: {e}"
                        )

            return OpenAPISpec(
                openapi=spec_dict["openapi"],
                info=spec_dict["info"],
                servers=spec_dict.get("servers", []),
                operations=operations,
                components=spec_dict.get("components", {}),
            )

        except OpenAPIError:
            raise
        except Exception as e:
            raise OpenAPIError(
                message=f"Failed to parse OpenAPI specification: {str(e)}",
                suggestion="Check that the specification is valid and well-formed",
                context={"error_type": type(e).__name__},
            )

    def _parse_operation(
        self, path: str, method: str, operation_data: Dict[str, Any]
    ) -> OpenAPIOperation:
        """Parse a single OpenAPI operation."""
        # Extract parameters
        parameters = []
        for param_data in operation_data.get("parameters", []):
            if "$ref" in param_data:
                # For simplicity, skip references for now
                continue

            param = ParameterInfo(
                name=param_data["name"],
                location=param_data["in"],
                required=param_data.get("required", False),
                schema_=param_data.get("schema", {}),
                description=param_data.get("description"),
            )
            parameters.append(param)

        # Extract request body
        request_body = None
        request_body_data = operation_data.get("requestBody")
        if request_body_data and "$ref" not in request_body_data:
            content_schema = {}
            content = request_body_data.get("content", {})
            for media_type, media_data in content.items():
                if "schema" in media_data:
                    content_schema[media_type] = media_data["schema"]

            request_body = RequestBodyInfo(
                required=request_body_data.get("required", False),
                content_schema=content_schema,
                description=request_body_data.get("description"),
            )

        # Extract responses
        responses = {}
        for status_code, response_data in operation_data.get("responses", {}).items():
            if "$ref" in response_data:
                # For simplicity, skip references for now
                continue

            content_schema = {}
            content = response_data.get("content", {})
            for media_type, media_data in content.items():
                if "schema" in media_data:
                    content_schema[media_type] = media_data["schema"]

            responses[status_code] = ResponseInfo(
                description=response_data.get("description"),
                content_schema=content_schema,
            )

        return OpenAPIOperation(
            path=path,
            method=method.upper(),
            operation_id=operation_data.get("operationId"),
            summary=operation_data.get("summary"),
            description=operation_data.get("description"),
            tags=operation_data.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
        )

    def get_operations(self) -> List[OpenAPIOperation]:
        """Get all available operations."""
        return self.spec.operations

    def get_operation(self, operation_id: str) -> Optional[OpenAPIOperation]:
        """Get operation by operation ID."""
        for operation in self.spec.operations:
            if operation.operation_id == operation_id:
                return operation
        return None

    def get_operations_by_tag(self, tag: str) -> List[OpenAPIOperation]:
        """Get operations by tag."""
        return [op for op in self.spec.operations if tag in op.tags]

    def find_operations(
        self, path: Optional[str] = None, method: Optional[str] = None
    ) -> List[OpenAPIOperation]:
        """Find operations by path and/or method."""
        operations = self.spec.operations

        if path:
            # Support partial path matching
            operations = [op for op in operations if path in op.path]

        if method:
            method = method.upper()
            operations = [op for op in operations if op.method == method]

        return operations

    async def execute_operation(
        self,
        operation_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """
        Execute an OpenAPI operation by operation ID.

        Args:
            operation_id: The operation ID to execute
            parameters: Parameters for the operation (path, query, header params)
            request_body: Request body data for POST/PUT/PATCH operations
            headers: Additional headers

        Returns:
            HttpResponse object with response data

        Raises:
            OpenAPIError: On operation execution failures
        """
        # Find the operation
        operation = self.get_operation(operation_id)
        if not operation:
            available_operations = [
                op.operation_id for op in self.spec.operations if op.operation_id
            ]
            raise OpenAPIError(
                message=f"Operation '{operation_id}' not found",
                suggestion=f"Use one of the available operations: {available_operations}",
                context={
                    "requested_operation": operation_id,
                    "available_operations": available_operations,
                },
                operation_id=operation_id,
            )

        return await self._execute_operation_obj(
            operation, parameters, request_body, headers
        )

    async def _execute_operation_obj(
        self,
        operation: OpenAPIOperation,
        parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """Execute an OpenAPI operation object."""
        parameters = parameters or {}

        try:
            # Build the URL with path parameters
            url = operation.path
            path_params = {}
            query_params = {}
            header_params = {}

            # Separate parameters by location
            for param in operation.parameters:
                if param.name in parameters:
                    value = parameters[param.name]

                    if param.location == "path":
                        path_params[param.name] = value
                    elif param.location == "query":
                        query_params[param.name] = value
                    elif param.location == "header":
                        header_params[param.name] = str(value)
                elif param.required:
                    raise OpenAPIError(
                        message=f"Required parameter '{param.name}' not provided",
                        suggestion=f"Provide the required {param.location} parameter '{param.name}'",
                        context={
                            "parameter_name": param.name,
                            "location": param.location,
                        },
                        operation_id=operation.operation_id,
                        schema_path=operation.path,
                    )

            # Replace path parameters in URL
            for param_name, param_value in path_params.items():
                url = url.replace(f"{{{param_name}}}", str(param_value))

            # Check if there are unresolved path parameters
            unresolved_params = re.findall(r"\{([^}]+)\}", url)
            if unresolved_params:
                raise OpenAPIError(
                    message=f"Path parameters not provided: {unresolved_params}",
                    suggestion=f"Provide values for path parameters: {', '.join(unresolved_params)}",
                    context={
                        "unresolved_params": unresolved_params,
                        "path": operation.path,
                    },
                    operation_id=operation.operation_id,
                    schema_path=operation.path,
                )

            # Combine headers
            combined_headers = headers or {}
            combined_headers.update(header_params)

            # Build the full URL using the parent class method
            full_url = self._build_url(url)

            # Create the request
            request = HttpRequest(
                method=operation.method,
                url=full_url,
                headers=combined_headers,
                params=query_params,
                json_data=request_body,
            )

            # Execute the request
            return await self.request(request)

        except OpenAPIError:
            raise
        except Exception as e:
            raise OpenAPIError(
                message=f"Failed to execute operation: {str(e)}",
                suggestion="Check your parameters and request body format",
                context={"error_type": type(e).__name__, "parameters": parameters},
                operation_id=operation.operation_id,
                schema_path=operation.path,
            )

    def generate_example_request(self, operation_id: str) -> Dict[str, Any]:
        """
        Generate an example request for an operation.

        Args:
            operation_id: The operation ID

        Returns:
            Dictionary with example parameters and request body
        """
        operation = self.get_operation(operation_id)
        if not operation:
            raise OpenAPIError(
                message=f"Operation '{operation_id}' not found",
                suggestion="Use a valid operation ID from the specification",
                operation_id=operation_id,
            )

        example = {"parameters": {}, "request_body": None}

        # Generate example parameters
        for param in operation.parameters:
            example_value = self._generate_example_value(param.schema_)
            example["parameters"][param.name] = example_value

        # Generate example request body
        if operation.request_body and operation.request_body.content_schema:
            # Use the first available content type
            content_type = next(iter(operation.request_body.content_schema))
            schema = operation.request_body.content_schema[content_type]
            example["request_body"] = self._generate_example_value(schema)

        return example

    def _generate_example_value(self, schema: Dict[str, Any]) -> Any:
        """Generate an example value from a JSON schema."""
        if not schema:
            return "example"

        schema_type = schema.get("type", "string")

        # Use provided examples or defaults
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        # Generate based on type
        if schema_type == "string":
            format_type = schema.get("format", "")
            if format_type == "date-time":
                return "2024-01-01T12:00:00Z"
            elif format_type == "date":
                return "2024-01-01"
            elif format_type == "email":
                return "user@example.com"
            elif format_type == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            else:
                return "example_string"
        elif schema_type == "integer":
            return 42
        elif schema_type == "number":
            return 3.14
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_example_value(items_schema)]
        elif schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Generate for required properties first
            for prop_name in required:
                if prop_name in properties:
                    result[prop_name] = self._generate_example_value(
                        properties[prop_name]
                    )

            # Add a few optional properties for completeness
            for prop_name, prop_schema in list(properties.items())[:3]:
                if prop_name not in result:
                    result[prop_name] = self._generate_example_value(prop_schema)

            return result

        return "example"


class OpenAPIClient(AsyncOpenAPIClient):
    """
    OpenAPI toolkit that extends HttpToolkit with OpenAPI schema parsing and operation execution.

    This class parses OpenAPI specifications and provides methods to execute operations
    with proper parameter validation and semantic error handling.
    """

    def execute_operation(
        self,
        operation_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """
        Execute an OpenAPI operation by operation ID (synchronous version).

        Args:
            operation_id: The operation ID to execute
            parameters: Parameters for the operation (path, query, header params)
            request_body: Request body data for POST/PUT/PATCH operations
            headers: Additional headers

        Returns:
            HttpResponse object with response data

        Raises:
            OpenAPIError: On operation execution failures
        """
        return asyncio.run(
            self.async_execute_operation(
                operation_id, parameters, request_body, headers
            )
        )

    async def async_execute_operation(
        self,
        operation_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """
        Execute an OpenAPI operation by operation ID (async version).

        Args:
            operation_id: The operation ID to execute
            parameters: Parameters for the operation (path, query, header params)
            request_body: Request body data for POST/PUT/PATCH operations
            headers: Additional headers

        Returns:
            HttpResponse object with response data

        Raises:
            OpenAPIError: On operation execution failures
        """
        return await super().execute_operation(
            operation_id, parameters, request_body, headers
        )


@overload
def create_openapi_client(
    spec_url_or_path: str,
    base_url: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    # Semantic authentication parameters
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    basic_auth: Optional[tuple[str, str]] = None,
    user_agent: Optional[str] = None,
    async_client: Literal[True] = ...,
) -> AsyncOpenAPIClient: ...


@overload
def create_openapi_client(
    spec_url_or_path: str,
    base_url: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    # Semantic authentication parameters
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    basic_auth: Optional[tuple[str, str]] = None,
    user_agent: Optional[str] = None,
    async_client: Literal[False] = ...,
) -> OpenAPIClient: ...


def create_openapi_client(
    spec_url_or_path: str,
    base_url: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    # Semantic authentication parameters
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    basic_auth: Optional[tuple[str, str]] = None,
    user_agent: Optional[str] = None,
    async_client: bool = False,
) -> Union[OpenAPIClient, AsyncOpenAPIClient]:
    """
    Create a new OpenAPIClient instance.

    Args:
        spec_url_or_path: URL or path to OpenAPI specification
        base_url: Base URL for all requests (optional)
        default_headers: Default headers to include in all requests
        timeout: Default timeout in seconds
        follow_redirects: Whether to follow redirects by default
        verify_ssl: Whether to verify SSL certificates
        api_key: API key for authentication
        api_key_header: Header name for API key (default: X-API-Key)
        bearer_token: Bearer token for Authorization header
        basic_auth: Tuple of (username, password) for basic auth
        user_agent: User-Agent header value
        async_client: Whether to return an async client instance

    Returns:
        OpenAPIClient or AsyncOpenAPIClient instance based on async_client parameter
    """
    params = locals()
    del params["async_client"]

    if async_client:
        return AsyncOpenAPIClient(**params)
    else:
        return OpenAPIClient(**params)
