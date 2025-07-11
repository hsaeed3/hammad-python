"""hammad._new

Main entrypoint for the `new` resource.
"""


class new:
    """Global factory resource for creating various objects available
    throughout the package. You can find most things in here."""

    from ..cache import create_cache as cache
    from ..data.configurations import (
        read_configuration_from_dotenv as configuration_from_dotenv,
        read_configuration_from_file as configuration_from_file,
        read_configuration_from_url as configuration_from_url,
        read_configuration_from_os_vars as configuration_from_os_vars,
        read_configuration_from_os_prefix as configuration_from_os_prefix,
    )
    from ..data.collections import (
        create_collection as collection,
    )
    from ..data.sql import (
        create_database as database,
    )
    from ..data.types import Text as text, Audio as audio, Image as image, File as file
    from ..genai import (
        create_embedding_model as embedding_model,
        create_language_model as language_model,
        create_agent as agent,
    )
    from ..logging import create_logger as logger
    from ..mcp import (
        MCPClient as mcp_client,
        MCPServerSseSettings as mcp_server_sse_settings,
        MCPClientSseSettings as mcp_client_sse_settings,
        MCPClientStreamableHttpSettings as mcp_client_http_settings,
        MCPServerStreamableHttpSettings as mcp_server_streamable_http_settings,
        MCPServerStdioSettings as mcp_server_stdio_settings,
        MCPClientStdioSettings as mcp_client_stdio_settings,
    )
    from ..service import (
        create_service as service,
        async_create_service as async_service,
    )
    from ..web import (
        create_http_client as http_client,
        create_openapi_client as openapi_client,
        create_search_client as search_client,
    )


__all__ = "new"
