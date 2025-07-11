"""hammad.mcp.servers"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .launcher import (
        launch_mcp_servers,
        MCPServerStdioSettings,
        MCPServerSseSettings,
        MCPServerStreamableHttpSettings,
    )

__all__ = (
    "launch_mcp_servers",
    "MCPServerStdioSettings",
    "MCPServerSseSettings",
    "MCPServerStreamableHttpSettings",
)

__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the servers module."""
    return list(__all__)
