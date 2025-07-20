"""ham.http.clients"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from .client import Client, create_client
    from .http_client import HttpClient, create_http_client
    from .openapi_client import OpenAPIClient, create_openapi_client
    from ..mcp.client.client import MCPClient, create_mcp_client


__all__ = (
    "Client",
    "create_client",
    "HttpClient",
    "create_http_client",
    "OpenAPIClient",
    "create_openapi_client",
    "MCPClient",
    "create_mcp_client",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the clients module."""
    return list(__all__)
