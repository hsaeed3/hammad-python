"""ham.http.mcp

```markdown
## `hammad-python-http`

This module contains various MCP resources and utilities.
```
"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
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
    # fastmcp
    "FastMCP",
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


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
