"""hammad.web"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .utils import (
        run_web_request,
        read_web_page,
        read_web_pages,
        search_web,
        search_news,
        extract_page_links,
    )
    from .http.client import AsyncHttpClient, HttpClient, create_http_client
    from .openapi.client import AsyncOpenAPIClient, OpenAPIClient, create_openapi_client
    from .search.client import AsyncSearchClient, SearchClient, create_search_client

__all__ = (
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "search_web",
    "search_news",
    "extract_page_links",
    "AsyncHttpClient",
    "HttpClient",
    "create_http_client",
    "AsyncOpenAPIClient",
    "OpenAPIClient",
    "create_openapi_client",
    "AsyncSearchClient",
    "SearchClient",
    "create_search_client",
)

__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the web module."""
    return list(__all__)
