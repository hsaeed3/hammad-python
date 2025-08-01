"""ham.http.mcp.servers"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ....core._internal import type_checking_importer  # type: ignore

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

__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the servers module."""
    return list(__all__)
