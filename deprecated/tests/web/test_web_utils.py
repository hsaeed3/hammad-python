import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from hammad.web.utils import (
    search_web,
    read_web_pages,
    read_web_page,
    search_news,
    extract_page_links,
)


class TestWebUtils:
    """Test suite for web utility functions."""

    def test_search_web_basic(self):
        """Test basic web search functionality."""
        results = search_web("python programming", max_results=5)

        assert isinstance(results, list)
        assert len(results) <= 5

        if results:  # If we got results
            result = results[0]
            assert "title" in result
            assert "href" in result
            assert "body" in result
            assert isinstance(result["title"], str)
            assert isinstance(result["href"], str)
            assert isinstance(result["body"], str)

    def test_search_web_empty_query(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_web("")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_web("   ")

    def test_search_web_with_options(self):
        """Test web search with various options."""
        # Mock the DDGS client to avoid rate limiting
        mock_results = [
            {
                "title": "Test Result 1",
                "href": "http://example.com/1",
                "body": "Test body 1",
            },
            {
                "title": "Test Result 2",
                "href": "http://example.com/2",
                "body": "Test body 2",
            },
            {
                "title": "Test Result 3",
                "href": "http://example.com/3",
                "body": "Test body 3",
            },
        ]

        with patch("hammad.web.utils._get_search_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.search_web = AsyncMock(return_value=mock_results[:3])
            mock_client.return_value = mock_instance

            results = search_web(
                "test query",
                max_results=3,
                region="us-en",
                safesearch="on",
                timelimit="d",
                backend="html",
            )

        assert isinstance(results, list)
        assert len(results) <= 3

    def test_search_news_basic(self):
        """Test basic news search functionality."""
        results = search_news("technology", max_results=3)

        assert isinstance(results, list)
        assert len(results) <= 3

        if results:  # If we got results
            result = results[0]
            # News results should have these fields
            expected_fields = ["title", "url", "body", "date", "source"]
            for field in expected_fields:
                assert field in result or any(
                    key.lower() == field.lower() for key in result.keys()
                )

    def test_search_news_empty_query(self):
        """Test that empty query raises ValueError for news search."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_news("")

    def test_search_news_with_options(self):
        """Test news search with various options."""
        results = search_news(
            "python",
            max_results=2,
            region="us-en",
            safesearch="moderate",
            timelimit="w",
        )

        assert isinstance(results, list)
        assert len(results) <= 2

    def test_read_web_page_basic(self):
        """Test basic web page reading functionality."""
        # Use a reliable test URL
        url = "https://httpbin.org/html"

        result = read_web_page(url)

        assert isinstance(result, dict)
        assert result["url"] == url
        assert "status_code" in result
        assert "content_type" in result
        assert "title" in result
        assert "text" in result
        assert "links" in result
        assert "images" in result
        assert "selected_elements" in result

        assert result["status_code"] == 200
        assert isinstance(result["text"], str)

    def test_read_web_page_with_options(self):
        """Test web page reading with various options."""
        url = "https://httpbin.org/html"

        result = read_web_page(
            url,
            extract_text=True,
            extract_links=True,
            extract_images=True,
            css_selector="h1",
        )

        assert isinstance(result, dict)
        assert result["url"] == url
        assert isinstance(result["links"], list)
        assert isinstance(result["images"], list)
        assert isinstance(result["selected_elements"], list)

    def test_read_web_page_with_headers(self):
        """Test web page reading with custom headers."""
        url = "https://httpbin.org/headers"
        custom_headers = {"X-Test-Header": "test-value"}

        result = read_web_page(url, headers=custom_headers)

        assert isinstance(result, dict)
        assert result["status_code"] == 200

    def test_read_web_pages_multiple(self):
        """Test reading multiple web pages concurrently."""
        urls = ["https://httpbin.org/html", "https://httpbin.org/json"]

        results = read_web_pages(urls, max_concurrent=2)

        assert isinstance(results, list)
        assert len(results) == len(urls)

        for i, result in enumerate(results):
            assert isinstance(result, dict)
            assert result["url"] == urls[i]
            if "error" not in result:
                assert "status_code" in result
                assert "text" in result

    def test_read_web_pages_empty_list(self):
        """Test reading empty list of URLs."""
        results = read_web_pages([])
        assert results == []

    def test_read_web_pages_with_duplicates(self):
        """Test reading web pages with duplicate URLs."""
        url = "https://httpbin.org/html"
        urls = [url, url, url]

        results = read_web_pages(urls)

        # Should deduplicate while preserving order
        assert len(results) == 1
        assert results[0]["url"] == url

    def test_read_web_pages_with_options(self):
        """Test reading multiple pages with various options."""
        urls = ["https://httpbin.org/html"]

        results = read_web_pages(
            urls,
            extract_text=True,
            extract_links=True,
            extract_images=True,
            css_selector="body",
            max_concurrent=1,
        )

        assert len(results) == 1
        result = results[0]
        assert isinstance(result["links"], list)
        assert isinstance(result["images"], list)
        assert isinstance(result["selected_elements"], list)

    def test_extract_page_links_basic(self):
        """Test basic link extraction functionality."""
        url = "https://httpbin.org/html"

        links = extract_page_links(url)

        assert isinstance(links, list)

        if links:  # If we got links
            link = links[0]
            assert "href" in link
            assert "original_href" in link
            assert "text" in link
            assert "title" in link
            assert "type" in link
            assert link["type"] in ["internal", "external"]

    def test_extract_page_links_with_filters(self):
        """Test link extraction with internal/external filters."""
        url = "https://httpbin.org/links/3"

        # Test extracting only internal links
        internal_links = extract_page_links(
            url, include_external=False, include_internal=True
        )

        assert isinstance(internal_links, list)
        for link in internal_links:
            assert link["type"] == "internal"

    def test_extract_page_links_with_css_selector(self):
        """Test link extraction with custom CSS selector."""
        url = "https://httpbin.org/html"

        links = extract_page_links(url, css_selector="a[href]")

        assert isinstance(links, list)

    def test_extract_page_links_with_custom_headers(self):
        """Test link extraction with custom headers."""
        url = "https://httpbin.org/html"
        custom_headers = {"User-Agent": "Test Bot"}

        links = extract_page_links(url, headers=custom_headers)

        assert isinstance(links, list)

    def test_extract_page_links_with_base_url(self):
        """Test link extraction with custom base URL."""
        url = "https://httpbin.org/html"
        base_url = "https://example.com"

        links = extract_page_links(url, base_url=base_url)

        assert isinstance(links, list)


class TestWebUtilsErrorHandling:
    """Test error handling in web utilities."""

    def test_read_web_page_invalid_url(self):
        """Test reading web page with invalid URL."""
        with pytest.raises(Exception):
            read_web_page("invalid-url")

    def test_read_web_page_nonexistent_url(self):
        """Test reading web page with nonexistent URL."""
        with pytest.raises(Exception):
            read_web_page("https://nonexistent-domain-12345.com")

    def test_read_web_pages_with_invalid_urls(self):
        """Test reading multiple pages with some invalid URLs."""
        urls = [
            "https://httpbin.org/html",
            "invalid-url",
            "https://nonexistent-domain-12345.com",
        ]

        results = read_web_pages(urls)

        assert len(results) == len(urls)

        # First URL should succeed
        assert "error" not in results[0] or results[0].get("status_code") is not None

        # Other URLs should have errors
        for result in results[1:]:
            assert "error" in result

    def test_extract_page_links_invalid_url(self):
        """Test link extraction with invalid URL."""
        with pytest.raises(Exception):
            extract_page_links("invalid-url")


class TestWebUtilsConfiguration:
    """Test configuration options for web utilities."""

    def test_search_web_different_regions(self):
        """Test web search with different regions."""
        query = "test"

        # Mock results for testing
        mock_results = [
            {"title": "Test Result", "href": "http://example.com", "body": "Test body"}
        ]

        # Test with different regions
        regions = ["wt-wt", "us-en", "uk-en"]

        with patch("hammad.web.utils._get_search_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.search_web = AsyncMock(return_value=mock_results)
            mock_client.return_value = mock_instance

            for region in regions:
                results = search_web(query, region=region, max_results=1)
                assert isinstance(results, list)

    def test_search_web_different_safesearch(self):
        """Test web search with different safesearch settings."""
        query = "test"

        # Mock results for testing
        mock_results = [
            {"title": "Test Result", "href": "http://example.com", "body": "Test body"}
        ]

        # Test with different safesearch settings
        safesearch_options = ["on", "moderate", "off"]

        with patch("hammad.web.utils._get_search_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.search_web = AsyncMock(return_value=mock_results)
            mock_client.return_value = mock_instance

            for safesearch in safesearch_options:
                results = search_web(query, safesearch=safesearch, max_results=1)
                assert isinstance(results, list)

    def test_read_web_page_timeout(self):
        """Test web page reading with custom timeout."""
        url = "https://httpbin.org/delay/1"

        # Should succeed with sufficient timeout
        result = read_web_page(url, timeout=5.0)
        assert result["status_code"] == 200

        # Should fail with very short timeout
        with pytest.raises(Exception):
            read_web_page(url, timeout=0.1)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
