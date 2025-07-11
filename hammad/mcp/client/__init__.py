"""hammad.mcp.client"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .client import (
        MCPClient,
        MCPClientService,
    )
    from .settings import (
        MCPClientSettings,
        MCPClientSseSettings,
        MCPClientStreamableHttpSettings,
        MCPClientStdioSettings,
    )

__all__ = (
    # hammad.mcp.client
    "MCPClient",
    # hammad.mcp.client.client_service
    "MCPClientService",
    # hammad.mcp.client.settings
    "MCPClientSettings",
    "MCPClientSseSettings",
    "MCPClientStreamableHttpSettings",
    "MCPClientStdioSettings",
)

__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the client module."""
    return list(__all__)
