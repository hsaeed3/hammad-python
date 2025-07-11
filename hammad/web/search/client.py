"""hammad.web.search.client"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Literal, Optional, Union, overload
from urllib.parse import urljoin, urlparse

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from ..models import (
    SearchResult,
    NewsResult,
    SearchResults,
    NewsResults,
    WebPageResult,
    WebPageErrorResult,
    WebPageResults,
    ExtractedLinks,
    ExtractedLink,
    LinkInfo,
    ImageInfo,
    SelectedElement,
)

__all__ = ("AsyncSearchClient", "SearchClient", "create_search_client")


class AsyncSearchClient:
    """
    Search client that provides web search and page parsing capabilities.

    This client uses lazy loading for DuckDuckGo search and selectolax HTML parsing
    to minimize import overhead and memory usage.
    """

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_concurrent: int = 5,
        user_agent: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ):
        """
        Initialize the SearchClient.

        Args:
            timeout: Default timeout for HTTP requests in seconds
            max_concurrent: Maximum number of concurrent requests for batch operations
            user_agent: User-Agent header for HTTP requests
            default_headers: Default headers to include in HTTP requests
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; SearchClient/1.0)"
        self.default_headers = default_headers or {}
        self.max_retries = max_retries

        # Lazy-loaded resources
        self._ddgs_client = None
        self._selectolax_parser_class = None

    def _get_duckduckgo_client(self):
        """Get a DuckDuckGo search client using lazy import and singleton pattern."""
        if self._ddgs_client is None:
            try:
                from ddgs import DDGS

                self._ddgs_client = DDGS
            except ImportError as e:
                raise ImportError(
                    "duckduckgo_search is required for web search functionality. "
                    "Install with: pip install duckduckgo-search"
                ) from e
        return self._ddgs_client

    def _get_selectolax_parser(self):
        """Get selectolax HTMLParser class using lazy import and singleton pattern."""
        if self._selectolax_parser_class is None:
            try:
                from selectolax.parser import HTMLParser

                self._selectolax_parser_class = HTMLParser
            except ImportError as e:
                raise ImportError(
                    "selectolax is required for HTML parsing functionality. "
                    "Install with: pip install selectolax"
                ) from e
        return self._selectolax_parser_class

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for HTTP requests."""
        headers = {"User-Agent": self.user_agent}
        headers.update(self.default_headers)
        return headers

    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: Literal["on", "moderate", "off"] = "moderate",
        timelimit: Optional[Literal["d", "w", "m", "y"]] = None,
        backend: Literal["auto", "html", "lite"] = "auto",
        max_retries: Optional[int] = None,
    ) -> SearchResults:
        """
        (deprecated in favor of `web_search`)

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            region: Search region (default: "wt-wt" for worldwide)
            safesearch: Safe search setting (default: "moderate")
            timelimit: Time limit for results (d=day, w=week, m=month, y=year)
            backend: Search backend to use (default: "auto")
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of search result dictionaries with 'title', 'href', and 'body' keys

        Raises:
            ValueError: If query is empty
            Exception: If search fails after all retries
        """
        from rich import print

        print(
            "[bold yellow]WARNING: [/bold yellow] [yellow]Using `AsyncSearchClient.[bold light_salmon3]search[/bold light_salmon3]` is now deprecated in favor of `AsyncSearchClient.[bold light_salmon3]web_search[/bold light_salmon3]`[/yellow]"
        )
        return await self.web_search(
            query,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
        )

    async def web_search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: Literal["on", "moderate", "off"] = "moderate",
        timelimit: Optional[Literal["d", "w", "m", "y"]] = None,
        backend: Literal["auto", "html", "lite"] = "auto",
        max_retries: Optional[int] = None,
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
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of search result dictionaries with 'title', 'href', and 'body' keys

        Raises:
            ValueError: If query is empty
            Exception: If search fails after all retries
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        retries = max_retries if max_retries is not None else self.max_retries

        async def _do_search():
            DDGS = self._get_duckduckgo_client()
            with DDGS() as ddgs:
                raw_results = list(
                    ddgs.text(
                        keywords=query.strip(),
                        region=region,
                        safesearch=safesearch,
                        timelimit=timelimit,
                        backend=backend,
                        max_results=max_results,
                    )
                )

                # Convert raw results to SearchResult models
                search_results = [
                    SearchResult(
                        title=result.get("title", ""),
                        href=result.get("href", ""),
                        body=result.get("body", ""),
                    )
                    for result in raw_results
                ]

                return SearchResults(query=query.strip(), results=search_results)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        ):
            with attempt:
                return await _do_search()

    async def search_news(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: Literal["on", "moderate", "off"] = "moderate",
        timelimit: Optional[Literal["d", "w", "m"]] = None,
        max_retries: Optional[int] = None,
    ) -> NewsResults:
        """
        Search for news using DuckDuckGo news search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            region: Search region (default: "wt-wt" for worldwide)
            safesearch: Safe search setting (default: "moderate")
            timelimit: Time limit for results (d=day, w=week, m=month)
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of news result dictionaries with date, title, body, url, image, and source

        Raises:
            ValueError: If query is empty
            Exception: If search fails after all retries
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        retries = max_retries if max_retries is not None else self.max_retries

        async def _do_news_search():
            DDGS = self._get_duckduckgo_client()
            with DDGS() as ddgs:
                raw_results = list(
                    ddgs.news(
                        keywords=query.strip(),
                        region=region,
                        safesearch=safesearch,
                        timelimit=timelimit,
                        max_results=max_results,
                    )
                )

                # Convert raw results to NewsResult models
                news_results = [
                    NewsResult(
                        date=result.get("date", ""),
                        title=result.get("title", ""),
                        body=result.get("body", ""),
                        url=result.get("url", ""),
                        image=result.get("image", ""),
                        source=result.get("source", ""),
                    )
                    for result in raw_results
                ]

                return NewsResults(query=query.strip(), results=news_results)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        ):
            with attempt:
                return await _do_news_search()

    async def read_web_page(
        self,
        url: str,
        *,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        extract_text: bool = True,
        extract_links: bool = False,
        extract_images: bool = False,
        css_selector: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> WebPageResult:
        """
        Read and parse a single web page using selectolax.

        Args:
            url: URL to fetch and parse
            timeout: Request timeout in seconds (uses default if not provided)
            headers: Optional HTTP headers to send
            extract_text: Whether to extract text content (default: True)
            extract_links: Whether to extract links (default: False)
            extract_images: Whether to extract images (default: False)
            css_selector: Optional CSS selector to extract specific elements
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            Dictionary containing parsed content and metadata

        Raises:
            httpx.HTTPError: If request fails after all retries
            Exception: If parsing fails
        """
        effective_headers = self._get_default_headers()
        if headers:
            effective_headers.update(headers)

        request_timeout = timeout or self.timeout
        retries = max_retries if max_retries is not None else self.max_retries

        async def _do_fetch_and_parse():
            async with httpx.AsyncClient(
                timeout=request_timeout, follow_redirects=True
            ) as client:
                response = await client.get(url, headers=effective_headers)
                response.raise_for_status()

                # Parse HTML content
                HTMLParser = self._get_selectolax_parser()
                parser = HTMLParser(response.text)

                title = ""
                text = ""
                links = []
                images = []
                selected_elements = []

                # Extract title
                title_node = parser.css_first("title")
                if title_node:
                    title = title_node.text(strip=True)

                # Extract text content
                if extract_text:
                    if css_selector:
                        selected_nodes = parser.css(css_selector)
                        text = " ".join(
                            node.text(strip=True) for node in selected_nodes
                        )
                    else:
                        text = parser.text(strip=True)

                # Extract links
                if extract_links:
                    link_nodes = parser.css("a[href]")
                    links = [
                        LinkInfo(
                            href=node.attrs.get("href", ""),
                            text=node.text(strip=True),
                        )
                        for node in link_nodes
                        if node.attrs.get("href")
                    ]

                # Extract images
                if extract_images:
                    img_nodes = parser.css("img[src]")
                    images = [
                        ImageInfo(
                            src=node.attrs.get("src", ""),
                            alt=node.attrs.get("alt", ""),
                            title=node.attrs.get("title", ""),
                        )
                        for node in img_nodes
                        if node.attrs.get("src")
                    ]

                # Extract selected elements
                if css_selector:
                    selected_nodes = parser.css(css_selector)
                    selected_elements = [
                        SelectedElement(
                            tag=node.tag,
                            text=node.text(strip=True),
                            html=node.html,
                            attributes=dict(node.attributes),
                        )
                        for node in selected_nodes
                    ]

                return WebPageResult(
                    url=url,
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type", ""),
                    title=title,
                    text=text,
                    links=links,
                    images=images,
                    selected_elements=selected_elements,
                )

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        ):
            with attempt:
                return await _do_fetch_and_parse()

    async def read_web_pages(
        self,
        urls: List[str],
        *,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        extract_text: bool = True,
        extract_links: bool = False,
        extract_images: bool = False,
        css_selector: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> WebPageResults:
        """
        Read and parse multiple web pages concurrently using selectolax.

        Args:
            urls: List of URLs to fetch and parse
            timeout: Request timeout in seconds (uses default if not provided)
            headers: Optional HTTP headers to send
            extract_text: Whether to extract text content (default: True)
            extract_links: Whether to extract links (default: False)
            extract_images: Whether to extract images (default: False)
            css_selector: Optional CSS selector to extract specific elements
            max_concurrent: Maximum number of concurrent requests (uses default if not provided)
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of dictionaries containing parsed content and metadata

        Raises:
            Exception: If any critical error occurs
        """
        if not urls:
            return []

        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)

        # Create semaphore for concurrency control
        concurrent_limit = max_concurrent or self.max_concurrent
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def fetch_page(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.read_web_page(
                        url=url,
                        timeout=timeout,
                        headers=headers,
                        extract_text=extract_text,
                        extract_links=extract_links,
                        extract_images=extract_images,
                        css_selector=css_selector,
                        max_retries=max_retries,
                    )
                except Exception as e:
                    return WebPageErrorResult(
                        url=url,
                        error=str(e),
                        status_code=None,
                        content_type="",
                        title="",
                        text="",
                        links=[],
                        images=[],
                        selected_elements=[],
                    )

        # Execute all requests concurrently
        tasks = [fetch_page(url) for url in unique_urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return WebPageResults(urls=unique_urls, results=results)

    async def extract_page_links(
        self,
        url: str,
        *,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        css_selector: str = "a[href]",
        include_external: bool = True,
        include_internal: bool = True,
        base_url: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> ExtractedLinks:
        """
        Extract links from a web page using selectolax.

        Args:
            url: URL to fetch and extract links from
            timeout: Request timeout in seconds (uses default if not provided)
            headers: Optional HTTP headers to send
            css_selector: CSS selector for links (default: "a[href]")
            include_external: Whether to include external links (default: True)
            include_internal: Whether to include internal links (default: True)
            base_url: Base URL for resolving relative links (uses page URL if not provided)
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of link dictionaries with href, text, title, and type (internal/external)

        Raises:
            httpx.HTTPError: If request fails after all retries
            Exception: If parsing fails
        """
        effective_headers = self._get_default_headers()
        if headers:
            effective_headers.update(headers)

        request_timeout = timeout or self.timeout
        retries = max_retries if max_retries is not None else self.max_retries

        async def _do_extract_links():
            async with httpx.AsyncClient(
                timeout=request_timeout, follow_redirects=True
            ) as client:
                response = await client.get(url, headers=effective_headers)
                response.raise_for_status()

                # Parse HTML content
                HTMLParser = self._get_selectolax_parser()
                parser = HTMLParser(response.text)

                # Use provided base_url or extract from the page
                effective_base_url = base_url or url

                # Get the domain for internal/external classification
                parsed_base = urlparse(effective_base_url)
                base_domain = parsed_base.netloc

                # Extract links
                link_nodes = parser.css(css_selector)
                links = []

                for node in link_nodes:
                    href = node.attrs.get("href", "").strip()
                    if not href:
                        continue

                    # Resolve relative URLs
                    absolute_href = urljoin(effective_base_url, href)
                    parsed_href = urlparse(absolute_href)

                    # Determine if link is internal or external
                    is_internal = (
                        parsed_href.netloc == base_domain or not parsed_href.netloc
                    )
                    link_type = "internal" if is_internal else "external"

                    # Filter based on include flags
                    if (is_internal and not include_internal) or (
                        not is_internal and not include_external
                    ):
                        continue

                    link_info = ExtractedLink(
                        href=absolute_href,
                        original_href=href,
                        text=node.text(strip=True),
                        title=node.attrs.get("title", ""),
                        type=link_type,
                    )

                    links.append(link_info)

                return ExtractedLinks(url=url, results=links)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        ):
            with attempt:
                return await _do_extract_links()


class SearchClient:
    """
    Synchronous wrapper around AsyncSearchClient.

    This class provides a synchronous interface to the search functionality
    by running async operations in an event loop.
    """

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_concurrent: int = 5,
        user_agent: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ):
        """
        Initialize the SearchClient.

        Args:
            timeout: Default timeout for HTTP requests in seconds
            max_concurrent: Maximum number of concurrent requests for batch operations
            user_agent: User-Agent header for HTTP requests
            default_headers: Default headers to include in HTTP requests
            max_retries: Maximum number of retry attempts for failed requests
        """
        self._async_client = AsyncSearchClient(
            timeout=timeout,
            max_concurrent=max_concurrent,
            user_agent=user_agent,
            default_headers=default_headers,
            max_retries=max_retries,
        )

    def _run_async(self, coro):
        """Run an async coroutine in a new event loop."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we need to use a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No event loop running, we can create our own
            return asyncio.run(coro)

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        backend: str = "api",
    ) -> SearchResults:
        """
        Synchronous web search using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            region: Search region (default: "wt-wt" for worldwide)
            safesearch: Safe search setting ("on", "moderate", "off")
            backend: Search backend ("api", "html", "lite")

        Returns:
            List of search result dictionaries with keys: title, href, body
        """
        return self._run_async(
            self._async_client.search(
                query,
                max_results=max_results,
                region=region,
                safesearch=safesearch,
                backend=backend,
            )
        )

    def get_page_content(
        self,
        url: str,
        *,
        timeout: Optional[float] = None,
        retries: int = 3,
        encoding: Optional[str] = None,
    ) -> str:
        """
        Synchronously fetch and return the text content of a web page.

        Args:
            url: URL of the web page to fetch
            timeout: Request timeout in seconds (uses client default if not specified)
            retries: Number of retry attempts for failed requests
            encoding: Text encoding to use (auto-detected if not specified)

        Returns:
            Plain text content of the web page
        """
        return self._run_async(
            self._async_client.get_page_content(
                url, timeout=timeout, retries=retries, encoding=encoding
            )
        )

    def extract_links(
        self,
        url: str,
        *,
        css_selector: str = "a[href]",
        include_internal: bool = True,
        include_external: bool = True,
        timeout: Optional[float] = None,
        retries: int = 3,
    ) -> ExtractedLinks:
        """
        Synchronously extract links from a web page.

        Args:
            url: URL of the web page to parse
            css_selector: CSS selector for link elements
            include_internal: Whether to include internal links
            include_external: Whether to include external links
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests

        Returns:
            List of link dictionaries with keys: href, original_href, text, title, type
        """
        return self._run_async(
            self._async_client.extract_links(
                url,
                css_selector=css_selector,
                include_internal=include_internal,
                include_external=include_external,
                timeout=timeout,
                retries=retries,
            )
        )

    def web_search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: Literal["on", "moderate", "off"] = "moderate",
        timelimit: Optional[Literal["d", "w", "m", "y"]] = None,
        backend: Literal["auto", "html", "lite"] = "auto",
        max_retries: Optional[int] = None,
    ) -> SearchResults:
        """
        Synchronously search the web using DuckDuckGo search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            region: Search region (default: "wt-wt" for worldwide)
            safesearch: Safe search setting (default: "moderate")
            timelimit: Time limit for results (d=day, w=week, m=month, y=year)
            backend: Search backend to use (default: "auto")
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of search result dictionaries with 'title', 'href', and 'body' keys

        Raises:
            ValueError: If query is empty
            Exception: If search fails after all retries
        """
        return self._run_async(
            self._async_client.web_search(
                query=query,
                max_results=max_results,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                backend=backend,
                max_retries=max_retries,
            )
        )

    def search_news(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "wt-wt",
        safesearch: Literal["on", "moderate", "off"] = "moderate",
        timelimit: Optional[Literal["d", "w", "m"]] = None,
        max_retries: Optional[int] = None,
    ) -> NewsResults:
        """
        Synchronously search for news using DuckDuckGo news search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            region: Search region (default: "wt-wt" for worldwide)
            safesearch: Safe search setting (default: "moderate")
            timelimit: Time limit for results (d=day, w=week, m=month)
            max_retries: Maximum number of retry attempts (uses instance default if not provided)

        Returns:
            List of news result dictionaries with date, title, body, url, image, and source

        Raises:
            ValueError: If query is empty
            Exception: If search fails after all retries
        """
        return self._run_async(
            self._async_client.search_news(
                query=query,
                max_results=max_results,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_retries=max_retries,
            )
        )

    def read_web_page(
        self,
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
        Synchronously read and parse a single web page using selectolax.

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
        return self._run_async(
            self._async_client.read_web_page(
                url=url,
                timeout=timeout,
                headers=headers,
                extract_text=extract_text,
                extract_links=extract_links,
                extract_images=extract_images,
                css_selector=css_selector,
            )
        )

    def read_web_pages(
        self,
        urls: List[str],
        *,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        extract_text: bool = True,
        extract_links: bool = False,
        extract_images: bool = False,
        css_selector: Optional[str] = None,
        max_concurrent: Optional[int] = None,
    ) -> WebPageResults:
        """
        Synchronously read and parse multiple web pages concurrently using selectolax.

        Args:
            urls: List of URLs to fetch and parse
            timeout: Request timeout in seconds (default: 30.0)
            headers: Optional HTTP headers to send
            extract_text: Whether to extract text content (default: True)
            extract_links: Whether to extract links (default: False)
            extract_images: Whether to extract images (default: False)
            css_selector: Optional CSS selector to extract specific elements
            max_concurrent: Maximum concurrent requests (uses client default if not specified)

        Returns:
            List of dictionaries containing parsed content and metadata for each URL

        Raises:
            httpx.HTTPError: If requests fail
            Exception: If parsing fails
        """
        return self._run_async(
            self._async_client.read_web_pages(
                urls=urls,
                timeout=timeout,
                headers=headers,
                extract_text=extract_text,
                extract_links=extract_links,
                extract_images=extract_images,
                css_selector=css_selector,
                max_concurrent=max_concurrent,
            )
        )

    def extract_page_links(
        self,
        url: str,
        *,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        css_selector: str = "a[href]",
        include_internal: bool = True,
        include_external: bool = True,
        base_url: Optional[str] = None,
    ) -> ExtractedLinks:
        """
        Synchronously extract all links from a web page.

        Args:
            url: URL to fetch and extract links from
            timeout: Request timeout in seconds (default: 30.0)
            headers: Optional HTTP headers to send
            css_selector: CSS selector for link elements (default: "a[href]")
            include_internal: Whether to include internal links (default: True)
            include_external: Whether to include external links (default: True)
            base_url: Base URL for resolving relative links (uses page URL if not provided)

        Returns:
            List of link dictionaries with 'href', 'original_href', 'text', 'title', and 'type' keys

        Raises:
            httpx.HTTPError: If request fails
            Exception: If parsing fails
        """
        return self._run_async(
            self._async_client.extract_page_links(
                url=url,
                timeout=timeout,
                headers=headers,
                css_selector=css_selector,
                include_internal=include_internal,
                include_external=include_external,
                base_url=base_url,
            )
        )

    def close(self):
        """Close the underlying async client."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


@overload
def create_search_client(
    *,
    timeout: float = 30.0,
    max_concurrent: int = 5,
    user_agent: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    async_client: Literal[True],
) -> AsyncSearchClient: ...


@overload
def create_search_client(
    *,
    timeout: float = 30.0,
    max_concurrent: int = 5,
    user_agent: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    async_client: Literal[False] = ...,
) -> SearchClient: ...


def create_search_client(
    *,
    timeout: float = 30.0,
    max_concurrent: int = 5,
    user_agent: Optional[str] = None,
    default_headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    async_client: bool = False,
) -> Union[SearchClient, AsyncSearchClient]:
    """
    Create a new SearchClient instance.

    Args:
        timeout: Default timeout for HTTP requests in seconds
        max_concurrent: Maximum number of concurrent requests for batch operations
        user_agent: User-Agent header for HTTP requests
        default_headers: Default headers to include in HTTP requests
        max_retries: Maximum number of retry attempts for failed requests
        async_client: Whether to return an async client instance

    Returns:
        SearchClient or AsyncSearchClient instance based on async_client parameter
    """
    params = locals()
    del params["async_client"]

    if async_client:
        return AsyncSearchClient(**params)
    else:
        return SearchClient(**params)
