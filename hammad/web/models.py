"""hammad.web.models

Output models for web search and parsing functionality.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Union
from typing_extensions import TypedDict, NotRequired


# -----------------------------------------------------------------------------
# Search Result Models
# -----------------------------------------------------------------------------


class SearchResult(TypedDict):
    """DuckDuckGo web search result."""

    title: str
    """Title of the search result."""

    href: str
    """URL of the search result."""

    body: str
    """Description/snippet of the search result."""


class NewsResult(TypedDict):
    """DuckDuckGo news search result."""

    date: str
    """Publication date of the news article."""

    title: str
    """Title of the news article."""

    body: str
    """Description/snippet of the news article."""

    url: str
    """URL of the news article."""

    image: str
    """Image URL associated with the news article."""

    source: str
    """Source/publisher of the news article."""


# -----------------------------------------------------------------------------
# Web Page Parsing Models
# -----------------------------------------------------------------------------


class LinkInfo(TypedDict):
    """Information about a link extracted from a web page."""

    href: str
    """Absolute URL of the link."""

    text: str
    """Text content of the link."""


class ImageInfo(TypedDict):
    """Information about an image extracted from a web page."""

    src: str
    """Source URL of the image."""

    alt: str
    """Alt text of the image."""

    title: str
    """Title attribute of the image."""


class SelectedElement(TypedDict):
    """Information about a selected element from CSS selector."""

    tag: str
    """HTML tag name of the element."""

    text: str
    """Text content of the element."""

    html: str
    """HTML content of the element."""

    attributes: Dict[str, str]
    """Attributes of the element."""


class WebPageResult(TypedDict):
    """Result from parsing a single web page."""

    url: str
    """URL of the parsed page."""

    status_code: int
    """HTTP status code of the response."""

    content_type: str
    """Content-Type header from the response."""

    title: str
    """Title of the web page."""

    text: str
    """Extracted text content of the page."""

    links: List[LinkInfo]
    """List of links found on the page."""

    images: List[ImageInfo]
    """List of images found on the page."""

    selected_elements: List[SelectedElement]
    """List of elements matching the CSS selector."""


class WebPageErrorResult(TypedDict):
    """Result from a failed web page parsing attempt."""

    url: str
    """URL that failed to be parsed."""

    error: str
    """Error message describing what went wrong."""

    status_code: None
    """Always None for error results."""

    content_type: str
    """Always empty string for error results."""

    title: str
    """Always empty string for error results."""

    text: str
    """Always empty string for error results."""

    links: List[LinkInfo]
    """Always empty list for error results."""

    images: List[ImageInfo]
    """Always empty list for error results."""

    selected_elements: List[SelectedElement]
    """Always empty list for error results."""


# -----------------------------------------------------------------------------
# Enhanced Link Models
# -----------------------------------------------------------------------------


class ExtractedLink(TypedDict):
    """Information about a link extracted with classification."""

    href: str
    """Absolute URL of the link."""

    original_href: str
    """Original href attribute value (may be relative)."""

    text: str
    """Text content of the link."""

    title: str
    """Title attribute of the link."""

    type: str
    """Type of link: 'internal' or 'external'."""


# -----------------------------------------------------------------------------
# HTTP Request Models
# -----------------------------------------------------------------------------


class HttpResponse(TypedDict):
    """HTTP response from web requests."""

    status_code: int
    """HTTP status code."""

    headers: Dict[str, str]
    """Response headers."""

    content: Union[str, bytes]
    """Response content."""

    url: str
    """Final URL after redirects."""

    elapsed: float
    """Time elapsed for the request in seconds."""

    json: NotRequired[Optional[Dict[str, Any]]]
    """Parsed JSON content if Content-Type is JSON."""

    text: NotRequired[str]
    """Text content if response is text-based."""


# -----------------------------------------------------------------------------
# Batch Operation Models
# -----------------------------------------------------------------------------


WebPageResults = List[Union[WebPageResult, WebPageErrorResult]]
"""Results from batch web page parsing operations."""

SearchResults = List[SearchResult]
"""Results from web search operations."""

NewsResults = List[NewsResult]
"""Results from news search operations."""

ExtractedLinks = List[ExtractedLink]
"""Results from link extraction operations."""


__all__ = (
    # Search models
    "SearchResult",
    "NewsResult",
    "SearchResults",
    "NewsResults",
    # Web page models
    "LinkInfo",
    "ImageInfo",
    "SelectedElement",
    "WebPageResult",
    "WebPageErrorResult",
    "WebPageResults",
    # Link extraction models
    "ExtractedLink",
    "ExtractedLinks",
    # HTTP models
    "HttpResponse",
)
