"""ham.http.clients.client

Unified client implementation with protocol inference.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Union, Literal, overload
from urllib.parse import urlparse

import httpx
import strawberry
from strawberry.schema import Schema

from ..core import (
    Authorization,
    Protocol,
    HttpMethod,
    Request,
    ProtocolType,
    HttpMethodType,
)
from ..models import HttpResponse


class Client:
    """Unified client with automatic protocol and method inference."""

    def __init__(
        self,
        *,
        auth: Optional[Authorization] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        **kwargs,
    ):
        self.auth = auth or Authorization()
        self.timeout = timeout
        self.default_headers = headers or {}
        self.verify_ssl = verify_ssl

        # HTTP client
        self._http_client = httpx.AsyncClient(
            timeout=timeout, verify=verify_ssl, headers=self.default_headers, **kwargs
        )

    # Overloads for better type inference
    @overload
    async def send(
        self,
        url: str,
        *,
        request: Optional[Dict[str, Any]] = None,
        infer_protocol: Literal[True] = True,
        infer_method_type: Literal[True] = True,
        **kwargs,
    ) -> Any: ...

    @overload
    async def send(
        self,
        url: str,
        *,
        request: Request,
        infer_protocol: bool = True,
        infer_method_type: bool = True,
        **kwargs,
    ) -> Any: ...

    async def send(
        self,
        url: str,
        *,
        request: Optional[Union[Dict[str, Any], Request]] = None,
        infer_protocol: bool = True,
        infer_method_type: bool = True,
        **kwargs,
    ) -> Any:
        """Send a request with automatic protocol and method inference."""

        # Convert dict request to Request object
        if isinstance(request, dict):
            request = Request(**request)
        elif request is None:
            request = Request()

        # Infer protocol if requested
        if infer_protocol:
            protocol = self._infer_protocol(url, request)
        else:
            protocol = request.protocol or Protocol.HTTP

        # Infer method if requested and not specified
        if infer_method_type and not request.method:
            method = self._infer_method(url, request)
        else:
            method = request.method or HttpMethod.GET

        # Update request with inferred values
        request.protocol = protocol
        request.method = method
        request.url = url

        # Route to appropriate client method
        if protocol == Protocol.HTTP:
            return await self._send_http(request, **kwargs)
        elif protocol == Protocol.GRAPHQL:
            return await self._send_graphql(request, **kwargs)
        elif protocol == Protocol.OPENAPI:
            return await self._send_openapi(request, **kwargs)
        elif protocol == Protocol.MCP:
            return await self._send_mcp(request, **kwargs)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    def send_sync(
        self,
        url: str,
        *,
        request: Optional[Union[Dict[str, Any], Request]] = None,
        infer_protocol: bool = True,
        infer_method_type: bool = True,
        **kwargs,
    ) -> Any:
        """Synchronous wrapper for send method."""
        return asyncio.run(
            self.send(
                url,
                request=request,
                infer_protocol=infer_protocol,
                infer_method_type=infer_method_type,
                **kwargs,
            )
        )

    def _infer_protocol(self, url: str, request: Request) -> Protocol:
        """Infer protocol from URL and request context."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Check for GraphQL endpoints
        if "/graphql" in path or "/graph" in path:
            return Protocol.GRAPHQL

        # Check for OpenAPI/Swagger endpoints
        if any(x in path for x in ["/api/", "/swagger", "/openapi"]):
            return Protocol.OPENAPI

        # Check for MCP endpoints
        if "/mcp" in path or "mcp" in parsed.hostname or "":
            return Protocol.MCP

        # Default to HTTP
        return Protocol.HTTP

    def _infer_method(self, url: str, request: Request) -> HttpMethod:
        """Infer HTTP method from URL path and request body."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Check for common RESTful patterns
        if any(x in path for x in ["/create", "/add", "/new"]):
            return HttpMethod.POST
        elif any(x in path for x in ["/update", "/edit", "/put"]):
            return HttpMethod.PUT
        elif any(x in path for x in ["/delete", "/remove"]):
            return HttpMethod.DELETE
        elif any(x in path for x in ["/patch", "/modify"]):
            return HttpMethod.PATCH

        # Check if request has body data
        if request.body is not None:
            return HttpMethod.POST

        # Default to GET
        return HttpMethod.GET

    async def _send_http(self, request: Request, **kwargs) -> HttpResponse:
        """Send HTTP request."""
        # Apply authentication
        headers = request.headers or {}
        headers.update(self._get_auth_headers())

        # Prepare request parameters
        request_params = {
            "method": request.method.value,
            "url": request.url,
            "headers": headers,
            "timeout": request.timeout or self.timeout,
        }

        # Add body/params based on method
        if request.method in [HttpMethod.GET, HttpMethod.HEAD, HttpMethod.OPTIONS]:
            if request.query_params:
                request_params["params"] = request.query_params
        else:
            if request.body:
                if isinstance(request.body, dict):
                    request_params["json"] = request.body
                else:
                    request_params["content"] = request.body
            if request.query_params:
                request_params["params"] = request.query_params

        # Make request
        response = await self._http_client.request(**request_params)

        # Parse response
        try:
            json_data = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else None
            )
        except:
            json_data = None

        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
            elapsed=response.elapsed.total_seconds(),
            json_data=json_data,
            text=response.text,
        )

    async def _send_graphql(self, request: Request, **kwargs) -> Any:
        """Send GraphQL request."""
        # GraphQL requests are typically POST to /graphql endpoint
        graphql_request = Request(
            protocol=Protocol.HTTP,
            method=HttpMethod.POST,
            url=request.url,
            headers={**(request.headers or {}), "Content-Type": "application/json"},
            body={
                "query": request.body.get("query")
                if isinstance(request.body, dict)
                else str(request.body),
                "variables": request.body.get("variables", {})
                if isinstance(request.body, dict)
                else {},
            },
            timeout=request.timeout,
        )

        response = await self._send_http(graphql_request, **kwargs)

        # Parse GraphQL response
        if response.json_data:
            return response.json_data
        else:
            raise ValueError(f"Invalid GraphQL response: {response.text}")

    async def _send_openapi(self, request: Request, **kwargs) -> Any:
        """Send OpenAPI request."""
        # For now, treat OpenAPI requests like regular HTTP
        return await self._send_http(request, **kwargs)

    async def _send_mcp(self, request: Request, **kwargs) -> Any:
        """Send MCP request."""
        # MCP (Model Context Protocol) implementation would go here
        # For now, treat like HTTP
        return await self._send_http(request, **kwargs)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth configuration."""
        headers = {}

        if self.auth.type == "bearer" and self.auth.token:
            headers["Authorization"] = f"Bearer {self.auth.token}"
        elif self.auth.type == "basic" and self.auth.username and self.auth.password:
            import base64

            credentials = base64.b64encode(
                f"{self.auth.username}:{self.auth.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif self.auth.type == "api_key" and self.auth.api_key:
            header_name = self.auth.header_name or "X-API-Key"
            headers[header_name] = self.auth.api_key

        return headers

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self._http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_client(
    *,
    auth: Optional[Authorization] = None,
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
    **kwargs,
) -> Client:
    """Create a new HTTP client with unified protocol support.

    A client provides automatic protocol inference and method detection for HTTP,
    GraphQL, OpenAPI, and MCP requests. It handles authentication, timeouts,
    and request/response processing seamlessly.

    Args:
        auth: Authentication configuration (bearer, basic, api_key, or none)
        timeout: Request timeout in seconds (default: 30.0)
        headers: Default headers to include with all requests
        verify_ssl: Whether to verify SSL certificates (default: True)
        **kwargs: Additional parameters passed to the underlying HTTPX client
            Common options include:
            - proxies: Dict of proxy configurations
            - cookies: Dict of cookies to include
            - max_redirects: Maximum number of redirects to follow
            - http2: Enable HTTP/2 support (bool)
            - limits: Connection pool limits
            - transport: Custom transport
            - mounts: Custom transport mounts
            - base_url: Base URL for relative requests

    Returns:
        Client instance ready to make requests

    Examples:
        Basic client:
        >>> client = create_client()
        >>> response = await client.send("https://api.example.com/data")

        Client with authentication:
        >>> auth = Authorization(type="bearer", token="your-token")
        >>> client = create_client(auth=auth)

        Client with custom configuration:
        >>> client = create_client(
        ...     timeout=60.0,
        ...     headers={"User-Agent": "MyApp/1.0"},
        ...     verify_ssl=False,
        ...     http2=True,
        ...     max_redirects=10,
        ...     proxies={"http://": "http://proxy:8080"}
        ... )

        Client with base URL and cookies:
        >>> client = create_client(
        ...     base_url="https://api.example.com",
        ...     cookies={"session": "abc123"},
        ...     timeout=45.0
        ... )

        Using with context manager:
        >>> async with create_client() as client:
        ...     response = await client.send("/graphql",
        ...                                 request={"query": "{ user { name } }"})
    """
    return Client(
        auth=auth,
        timeout=timeout,
        headers=headers,
        verify_ssl=verify_ssl,
        **kwargs,
    )


__all__ = ["Client", "create_client"]
