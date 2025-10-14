"""ham.http.core

Core models and types for the unified HTTP interface.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, List, Literal, Optional, Union, Callable, get_type_hints
from enum import Enum

from pydantic import BaseModel, Field

# Literal types for protocols
ProtocolType = Literal["http", "graphql", "openapi", "mcp"]

# Literal types for HTTP methods
HttpMethodType = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Literal types for authentication
AuthMethodType = Literal["none", "basic", "bearer", "api_key", "oauth2"]


class Protocol(str, Enum):
    """Supported protocols."""

    HTTP = "http"
    GRAPHQL = "graphql"
    OPENAPI = "openapi"
    MCP = "mcp"


class HttpMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(str, Enum):
    """Authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class Authorization(BaseModel):
    """Authorization configuration."""

    type: Union[AuthType, AuthMethodType] = AuthType.NONE
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    header_name: Optional[str] = None
    oauth_config: Optional[Dict[str, Any]] = None


class Request(BaseModel):
    """Unified request model."""

    protocol: Union[Protocol, ProtocolType] = Protocol.HTTP
    method: Optional[Union[HttpMethod, HttpMethodType]] = None
    url: Optional[str] = None
    path: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    timeout: Optional[float] = None


class RouteInfo(BaseModel):
    """Information about a registered route."""

    path: str
    function: Callable
    methods: List[HttpMethod]
    protocols: List[Protocol]
    parameters: Dict[str, Any]
    return_type: Optional[type] = None


def infer_http_method(func: Callable) -> HttpMethod:
    """Infer HTTP method from function signature and name."""
    func_name = func.__name__.lower()

    # Check function name prefixes
    if func_name.startswith(("get_", "list_", "fetch_", "read_")):
        return HttpMethod.GET
    elif func_name.startswith(("post_", "create_", "add_", "insert_")):
        return HttpMethod.POST
    elif func_name.startswith(("put_", "update_", "replace_")):
        return HttpMethod.PUT
    elif func_name.startswith(("delete_", "remove_", "del_")):
        return HttpMethod.DELETE
    elif func_name.startswith(("patch_", "modify_")):
        return HttpMethod.PATCH

    # Check function signature
    sig = inspect.signature(func)
    has_body_params = any(
        param.annotation != inspect.Parameter.empty
        and param.annotation not in (str, int, float, bool)
        and param.name not in ("self", "cls")
        for param in sig.parameters.values()
    )

    return HttpMethod.POST if has_body_params else HttpMethod.GET


def extract_function_metadata(func: Callable) -> Dict[str, Any]:
    """Extract metadata from a function for route registration."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    parameters = {}
    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue

        param_info = {
            "name": name,
            "annotation": type_hints.get(name, param.annotation),
            "default": param.default
            if param.default != inspect.Parameter.empty
            else None,
            "required": param.default == inspect.Parameter.empty,
        }
        parameters[name] = param_info

    return {
        "parameters": parameters,
        "return_type": type_hints.get("return", sig.return_annotation),
    }


__all__ = [
    "Protocol",
    "HttpMethod",
    "AuthType",
    "ProtocolType",
    "HttpMethodType",
    "AuthMethodType",
    "Authorization",
    "Request",
    "RouteInfo",
    "infer_http_method",
    "extract_function_metadata",
]
