"""hammad.web.utils"""

import asyncio
from typing import Any, Dict, Optional, Union, Literal, List, overload, TYPE_CHECKING

if TYPE_CHECKING:
    from .http.client import HttpResponse

from .models import (
    SearchResults,
    NewsResults,
    WebPageResult,
    WebPageResults,
    ExtractedLinks,
    HttpResponse as HttpResponseModel,
)

__all__ = (
    "run_web_request",
    "run_web_search",
    "read_web_page",
    "read_web_pages",
    "run_news_search",
    "extract_web_page_links",
)


# Module-level singleton for performance
_search_client = None


def _get_search_client():
    """Get a SearchClient instance using lazy import and singleton pattern."""
    global _search_client
    if _search_client is None:
        from .search.client import AsyncSearchClient as SearchClient

        _search_client = SearchClient()
    return _search_client


@overload
def run_web_request(
    type: Literal["http"],
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, Any]] = None,
    content: Optional[Union[str, bytes]] = None,
    timeout: Optional[float] = None,
    follow_redirects: bool = True,
    base_url: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
    # Semantic authentication parameters
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    basic_auth: Optional[tuple[str, str]] = None,
    user_agent: Optional[str] = None,
    retry_attempts: int = 0,
    retry_delay: float = 1.0,
) -> "HttpResponse": ...


@overload
def run_web_request(
    type: Literal["openapi"],
    openapi_spec: Union[str, Dict[str, Any]],
    operation_id: str,
    *,
    parameters: Optional[Dict[str, Any]] = None,
    request_body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    # Semantic authentication parameters
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    basic_auth: Optional[tuple[str, str]] = None,
    user_agent: Optional[str] = None,
) -> "HttpResponse": ...


def run_web_request(
    type: Literal["http", "openapi"], *args, **kwargs
) -> "HttpResponse":
    """
    Create and execute a request using either HTTP or OpenAPI toolkits.

    This function initializes the appropriate toolkit and sends the request,
    returning the HTTP response.

    Args:
        type: Type of request - "http" for direct HTTP requests or "openapi" for OpenAPI operations

    HTTP-specific args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        params: Query parameters
        json_data: JSON request body
        form_data: Form data
        content: Raw content
        timeout: Request timeout
        follow_redirects: Whether to follow redirects
        base_url: Base URL for requests
        default_headers: Default headers
        verify_ssl: Whether to verify SSL certificates

    OpenAPI-specific args:
        openapi_spec: OpenAPI specification (dict, JSON string, or YAML string)
        operation_id: OpenAPI operation ID to execute
        parameters: Operation parameters
        request_body: Request body for the operation
        headers: Additional headers
        base_url: Base URL override
        default_headers: Default headers
        timeout: Request timeout
        follow_redirects: Whether to follow redirects
        verify_ssl: Whether to verify SSL certificates

    Returns:
        HttpResponse object containing the response data

    Raises:
        ValueError: For invalid request type or missing required parameters
        HttpToolkitError: For HTTP-related errors
        OpenApiToolkitError: For OpenAPI-related errors
    """

    async def _run_web_request_async():
        if type == "http":
            if len(args) < 2:
                raise ValueError(
                    "HTTP requests require method and url as positional arguments"
                )

            method, url = args[0], args[1]

            # Import here to avoid circular imports
            from .http.client import HttpClient as HttpToolkit

            # Initialize the HTTP toolkit
            toolkit = HttpToolkit(
                base_url=kwargs.get("base_url"),
                default_headers=kwargs.get("default_headers", {}),
                timeout=kwargs.get("timeout", 30.0),
                follow_redirects=kwargs.get("follow_redirects", True),
                verify_ssl=kwargs.get("verify_ssl", True),
                api_key=kwargs.get("api_key"),
                api_key_header=kwargs.get("api_key_header", "X-API-Key"),
                bearer_token=kwargs.get("bearer_token"),
                basic_auth=kwargs.get("basic_auth"),
                user_agent=kwargs.get("user_agent"),
            )

            # Execute the request based on method
            if method.upper() == "GET":
                return await toolkit.get(
                    url,
                    headers=kwargs.get("headers"),
                    params=kwargs.get("params"),
                    timeout=kwargs.get("timeout"),
                    retry_attempts=kwargs.get("retry_attempts", 0),
                    retry_delay=kwargs.get("retry_delay", 1.0),
                )
            elif method.upper() == "POST":
                return await toolkit.post(
                    url,
                    headers=kwargs.get("headers"),
                    json_data=kwargs.get("json_data"),
                    form_data=kwargs.get("form_data"),
                    timeout=kwargs.get("timeout"),
                    retry_attempts=kwargs.get("retry_attempts", 0),
                )
            elif method.upper() == "PUT":
                return await toolkit.put(
                    url,
                    headers=kwargs.get("headers"),
                    json_data=kwargs.get("json_data"),
                    form_data=kwargs.get("form_data"),
                    timeout=kwargs.get("timeout"),
                    retry_attempts=kwargs.get("retry_attempts", 0),
                )
            elif method.upper() == "PATCH":
                return await toolkit.patch(
                    url,
                    headers=kwargs.get("headers"),
                    json_data=kwargs.get("json_data"),
                    form_data=kwargs.get("form_data"),
                    timeout=kwargs.get("timeout"),
                    retry_attempts=kwargs.get("retry_attempts", 0),
                )
            elif method.upper() == "DELETE":
                return await toolkit.delete(
                    url,
                    headers=kwargs.get("headers"),
                    timeout=kwargs.get("timeout"),
                    retry_attempts=kwargs.get("retry_attempts", 0),
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        elif type == "openapi":
            from .openapi.client import OpenAPIClient as OpenApiToolkit

            if len(args) < 2:
                raise ValueError(
                    "OpenAPI requests require openapi_spec and operation_id as positional arguments"
                )

            openapi_spec, operation_id = args[0], args[1]

            # Initialize the OpenAPI toolkit
            toolkit = OpenApiToolkit(
                openapi_spec=openapi_spec,
                base_url=kwargs.get("base_url"),
                default_headers=kwargs.get("default_headers"),
                timeout=kwargs.get("timeout", 30.0),
                follow_redirects=kwargs.get("follow_redirects", True),
                verify_ssl=kwargs.get("verify_ssl", True),
                api_key=kwargs.get("api_key"),
                api_key_header=kwargs.get("api_key_header", "X-API-Key"),
                bearer_token=kwargs.get("bearer_token"),
                basic_auth=kwargs.get("basic_auth"),
                user_agent=kwargs.get("user_agent"),
            )

            # Execute the OpenAPI operation
            return await toolkit.execute_operation(
                operation_id=operation_id,
                parameters=kwargs.get("parameters"),
                request_body=kwargs.get("request_body"),
                headers=kwargs.get("headers"),
            )

        else:
            raise ValueError(
                f"Invalid request type: {type}. Must be 'http' or 'openapi'"
            )

    return asyncio.run(_run_web_request_async())


def run_web_search(
    query: str,
    *,
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: Literal["on", "moderate", "off"] = "moderate",
    timelimit: Optional[Literal["d", "w", "m", "y"]] = None,
    backend: Literal["auto", "html", "lite"] = "auto",
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
) -> SearchResults:
    """
    Search the web using DuckDuckGo search.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        region: Search region (default: "wt-wt" for worldwide)
        safesearch: Safe search setting (default: "moderate")
        timelimit: Time limit for results (d=day, w=week, m=month, y=year)
        backend: Search backend to use (default: "auto")
        retry_attempts: Number of retry attempts for rate limit errors (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)

    Returns:
        List of search result dictionaries with 'title', 'href', and 'body' keys

    Raises:
        ValueError: If query is empty
        Exception: If search fails after all retries
    """

    async def _run_web_search_async():
        client = _get_search_client()
        return await client.web_search(
            query=query,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            backend=backend,
        )

    return asyncio.run(_run_web_search_async())


def read_web_page(
    url: str,
    *,
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None,
    extract_text: bool = True,
    extract_links: bool = False,
    extract_images: bool = False,
    css_selector: Optional[str] = None,
) -> WebPageResult:
    """
    Read and parse a single web page using selectolax.

    Args:
        url: URL to fetch and parse
        timeout: Request timeout in seconds (default: 30.0)
        headers: Optional HTTP headers to send
        extract_text: Whether to extract text content (default: True)
        extract_links: Whether to extract links (default: False)
        extract_images: Whether to extract images (default: False)
        css_selector: Optional CSS selector to extract specific elements

    Returns:
        Dictionary containing parsed content and metadata

    Raises:
        httpx.HTTPError: If request fails
        Exception: If parsing fails
    """

    async def _read_web_page_async():
        client = _get_search_client()
        return await client.read_web_page(
            url=url,
            timeout=timeout,
            headers=headers,
            extract_text=extract_text,
            extract_links=extract_links,
            extract_images=extract_images,
            css_selector=css_selector,
        )

    return asyncio.run(_read_web_page_async())


def read_web_pages(
    urls: List[str],
    *,
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None,
    extract_text: bool = True,
    extract_links: bool = False,
    extract_images: bool = False,
    css_selector: Optional[str] = None,
    max_concurrent: int = 5,
) -> WebPageResults:
    """
    Read and parse multiple web pages concurrently using selectolax.

    Args:
        urls: List of URLs to fetch and parse
        timeout: Request timeout in seconds (default: 30.0)
        headers: Optional HTTP headers to send
        extract_text: Whether to extract text content (default: True)
        extract_links: Whether to extract links (default: False)
        extract_images: Whether to extract images (default: False)
        css_selector: Optional CSS selector to extract specific elements
        max_concurrent: Maximum number of concurrent requests (default: 5)

    Returns:
        List of dictionaries containing parsed content and metadata

    Raises:
        Exception: If any critical error occurs
    """

    async def _read_web_pages_async():
        client = _get_search_client()
        return await client.read_web_pages(
            urls=urls,
            timeout=timeout,
            headers=headers,
            extract_text=extract_text,
            extract_links=extract_links,
            extract_images=extract_images,
            css_selector=css_selector,
            max_concurrent=max_concurrent,
        )

    return asyncio.run(_read_web_pages_async())


def run_news_search(
    query: str,
    *,
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: Literal["on", "moderate", "off"] = "moderate",
    timelimit: Optional[Literal["d", "w", "m"]] = None,
) -> NewsResults:
    """
    Search for news using DuckDuckGo news search.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        region: Search region (default: "wt-wt" for worldwide)
        safesearch: Safe search setting (default: "moderate")
        timelimit: Time limit for results (d=day, w=week, m=month)

    Returns:
        List of news result dictionaries with date, title, body, url, image, and source

    Raises:
        ValueError: If query is empty
        Exception: If search fails
    """

    async def _run_news_search_async():
        client = _get_search_client()
        return await client.search_news(
            query=query,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
        )

    return asyncio.run(_run_news_search_async())


def extract_web_page_links(
    url: str,
    *,
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None,
    css_selector: str = "a[href]",
    include_external: bool = True,
    include_internal: bool = True,
    base_url: Optional[str] = None,
) -> ExtractedLinks:
    """
    Extract links from a web page using selectolax.

    Args:
        url: URL to fetch and extract links from
        timeout: Request timeout in seconds (default: 30.0)
        headers: Optional HTTP headers to send
        css_selector: CSS selector for links (default: "a[href]")
        include_external: Whether to include external links (default: True)
        include_internal: Whether to include internal links (default: True)
        base_url: Base URL for resolving relative links (uses page URL if not provided)

    Returns:
        List of link dictionaries with href, text, title, and type (internal/external)

    Raises:
        httpx.HTTPError: If request fails
        Exception: If parsing fails
    """

    async def _extract_web_page_links_async():
        client = _get_search_client()
        return await client.extract_page_links(
            url=url,
            timeout=timeout,
            headers=headers,
            css_selector=css_selector,
            include_external=include_external,
            include_internal=include_internal,
            base_url=base_url,
        )

    return asyncio.run(_extract_web_page_links_async())
