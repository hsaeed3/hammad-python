"""
eval-interface.mcp
"""

from typing import TYPE_CHECKING
from ..._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .client.client import MCPClient, MCPClientSettings
    from .client.client_service import (
        MCPClientService,
        MCPClientServiceSse,
        MCPClientServiceStdio,
        MCPClientServiceStreamableHttp,
        MCPTool,
    )
    from .client.settings import (
        MCPClientSseSettings,
        MCPClientStdioSettings,
        MCPClientStreamableHttpSettings,
    )
    from .servers.launcher import (
        launch_mcp_servers,
        launch_sse_mcp_server,
        launch_stdio_mcp_server,
        launch_streamable_http_mcp_server,
        MCPServerService,
        SSEServerSettings,
        StdioServerSettings,
        StreamableHTTPServerSettings,
    )


__all__ = (
    # hammad.ai.mcp.client
    "MCPClient",
    "MCPClientSettings",
    "MCPClientService",
    "MCPClientServiceSse",
    "MCPClientServiceStdio",
    "MCPClientServiceStreamableHttp",
    "MCPTool",
    # hammad.ai.mcp.client.settings
    "MCPClientSseSettings",
    "MCPClientStdioSettings",
    "MCPClientStreamableHttpSettings",
    "SSEServerSettings",
    "StdioServerSettings",
    "StreamableHTTPServerSettings",
    "ServerSettings",
    # hammad.ai.mcp.servers.launcher'
    "launch_mcp_servers",
    "launch_sse_mcp_server",
    "launch_stdio_mcp_server",
    "launch_streamable_http_mcp_server",
    "MCPServerService",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
