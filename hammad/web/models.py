"""hammad.web.models

Output models for web search and parsing functionality.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Union

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Search Result Models
# -----------------------------------------------------------------------------


class SearchResult(BaseModel):
    """DuckDuckGo web search result."""

    title: str
    """Title of the search result."""

    href: str
    """URL of the search result."""

    body: str
    """Description/snippet of the search result."""


class NewsResult(BaseModel):
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


class LinkInfo(BaseModel):
    """Information about a link extracted from a web page."""

    href: str
    """Absolute URL of the link."""

    text: str
    """Text content of the link."""


class ImageInfo(BaseModel):
    """Information about an image extracted from a web page."""

    src: str
    """Source URL of the image."""

    alt: str
    """Alt text of the image."""

    title: str
    """Title attribute of the image."""


class SelectedElement(BaseModel):
    """Information about a selected element from CSS selector."""

    tag: str
    """HTML tag name of the element."""

    text: str
    """Text content of the element."""

    html: str
    """HTML content of the element."""

    attributes: Dict[str, str]
    """Attributes of the element."""


class WebPageResult(BaseModel):
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


class WebPageErrorResult(BaseModel):
    """Result from a failed web page parsing attempt."""

    url: str
    """URL that failed to be parsed."""

    error: str
    """Error message describing what went wrong."""

    status_code: Optional[int]
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


class ExtractedLink(BaseModel):
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


class HttpResponse(BaseModel):
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

    # NOTE: This is a workaround to avoid the issue with the `json` field
    # might consider moving to dataclasses
    json_data: Optional[Dict[str, Any]] = Field(alias="json")
    """Parsed JSON content if Content-Type is JSON."""

    text: str
    """Text content if response is text-based."""


# -----------------------------------------------------------------------------
# Batch Operation Models
# -----------------------------------------------------------------------------


class WebPageResults(BaseModel):
    """Results from batch web page parsing operations."""

    urls: List[str]
    """URLs used for the web page parsing operations."""

    results: List[Union[WebPageResult, WebPageErrorResult]]
    """List of results from batch web page parsing operations."""


class SearchResults(BaseModel):
    """Results from web search operations."""

    query: str
    """Query used for the web search operations."""

    results: List[SearchResult]
    """List of results from web search operations."""


class NewsResults(BaseModel):
    """Results from news search operations."""

    query: str
    """Query used for the news search operations."""

    results: List[NewsResult]
    """List of results from news search operations."""


class ExtractedLinks(BaseModel):
    """Results from link extraction operations."""

    url: str
    """URL used for the link extraction operations."""

    results: List[ExtractedLink]
    """List of results from link extraction operations."""


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
