"""
hammad.mcp
"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .client.client import (
        convert_mcp_tool_to_openai_tool,
        MCPClient,
        MCPClientService,
    )
    from .client.settings import (
        MCPClientStdioSettings,
        MCPClientSseSettings,
        MCPClientStreamableHttpSettings,
    )
    from .servers.launcher import (
        launch_mcp_servers,
        MCPServerService,
        MCPServerStdioSettings,
        MCPServerSseSettings,
        MCPServerStreamableHttpSettings,
    )


__all__ = (
    # hammad.mcp.client
    "MCPClient",
    "MCPClientService",
    "convert_mcp_tool_to_openai_tool",
    # hammad.mcp.client.settings
    "MCPClientStdioSettings",
    "MCPClientSseSettings",
    "MCPClientStreamableHttpSettings",
    # hammad.mcp.servers.launcher
    "launch_mcp_servers",
    "MCPServerService",
    "MCPServerStdioSettings",
    "MCPServerSseSettings",
    "MCPServerStreamableHttpSettings",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
