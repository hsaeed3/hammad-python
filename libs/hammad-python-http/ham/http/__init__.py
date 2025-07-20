"""ham.http

```markdown
## `hammad-python-http`

This module contains various HTTP - networking related resources,
components and utilities including a unified 'Client' & 'Server'
interface.
```
"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from .server import Server, create_server
    from .clients import (
        Client,
        HttpClient,
        OpenAPIClient,
        MCPClient,
        create_client,
        create_http_client,
        create_openapi_client,
        create_mcp_client,
    )
    from .core import (
        Authorization,
        Request,
        Protocol,
        HttpMethod,
        AuthType,
        ProtocolType,
        HttpMethodType,
        AuthMethodType,
    )
    from .models import HttpResponse
    from .service import (
        create_fast_service,
        async_create_fast_service,
        function_server,
        function_mcp_server,
    )
    from .search.client import (
        create_search_client,
        SearchClient,
        AsyncSearchClient,
    )
    from .utils import (
        run_web_request,
        read_web_page,
        read_web_pages,
        run_web_search,
        run_news_search,
        extract_web_page_links,
    )
    from .mcp.client.client import (
        convert_mcp_tool_to_openai_tool,
        MCPClient,
        MCPClientService,
    )
    from .mcp.client.settings import (
        MCPClientStdioSettings,
        MCPClientSseSettings,
        MCPClientStreamableHttpSettings,
    )
    from .mcp.servers.launcher import (
        launch_mcp_servers,
        MCPServerService,
        MCPServerStdioSettings,
        MCPServerSseSettings,
        MCPServerStreamableHttpSettings,
    )


__all__ = (
    # Main interfaces
    "Server",
    "Client",
    "HttpClient",
    "OpenAPIClient",
    "MCPClient",
    "create_server",
    "create_client",
    "create_http_client",
    "create_openapi_client",
    "create_mcp_client",
    # Core models
    "Authorization",
    "Request",
    "HttpResponse",
    # Enums and types
    "Protocol",
    "HttpMethod",
    "AuthType",
    "ProtocolType",
    "HttpMethodType",
    "AuthMethodType",
    # Service
    "create_fast_service",
    "async_create_fast_service",
    "function_server",
    "function_mcp_server",
    # Search
    "create_search_client",
    "SearchClient",
    "AsyncSearchClient",
    # Utils
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "run_web_search",
    "run_news_search",
    "extract_web_page_links",
    # MCP
    "convert_mcp_tool_to_openai_tool",
    "MCPClient",
    "MCPClientService",
    "MCPClientStdioSettings",
    "MCPClientSseSettings",
    "MCPClientStreamableHttpSettings",
    "launch_mcp_servers",
    "MCPServerService",
    "MCPServerStdioSettings",
    "MCPServerSseSettings",
    "MCPServerStreamableHttpSettings",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad module."""
    return __all__
