import pytest
from hammad.web.http.client import (
    AsyncHttpClient as HttpToolkit,
    HttpRequest,
    HttpResponse,
)

import asyncio
import json
from unittest.mock import AsyncMock, patch
from typing import Dict, Any
import httpx


# Mock server responses for testing
class MockResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        text: str = "",
        headers: Dict[str, str] = None,
        url: str = "https://api.example.com/test",
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or json.dumps(self._json_data)
        self.headers = headers or {"content-type": "application/json"}
        self.url = url
        self.request = AsyncMock()
        self.request.method = "GET"

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not self.is_success:
            raise httpx.HTTPStatusError(
                message=f"HTTP {self.status_code}", request=self.request, response=self
            )


@pytest.mark.asyncio
async def test_http_toolkit_init():
    """Test HttpToolkit initialization."""
    toolkit = HttpToolkit()
    assert toolkit.base_url is None
    assert toolkit.default_headers == {}
    assert toolkit.timeout == 30.0
    assert toolkit.follow_redirects is True
    assert toolkit.verify_ssl is True


@pytest.mark.asyncio
async def test_http_toolkit_init_with_base_url():
    """Test HttpToolkit initialization with base URL."""
    base_url = "https://api.example.com"
    toolkit = HttpToolkit(base_url=base_url)
    assert toolkit.base_url == base_url


@pytest.mark.asyncio
async def test_http_toolkit_invalid_base_url():
    """Test HttpToolkit initialization with invalid base URL."""
    with pytest.raises(Exception) as exc_info:
        HttpToolkit(base_url="invalid-url")
    assert "Invalid base URL" in str(exc_info.value)


@pytest.mark.asyncio
async def test_build_url():
    """Test URL building with base URL."""
    toolkit = HttpToolkit(base_url="https://api.example.com")

    # Test with relative path
    url = toolkit._build_url("users")
    assert url == "https://api.example.com/users"

    # Test with leading slash
    url = toolkit._build_url("/users")
    assert url == "https://api.example.com/users"

    # Test without base URL
    toolkit_no_base = HttpToolkit()
    url = toolkit_no_base._build_url("https://api.example.com/users")
    assert url == "https://api.example.com/users"


@pytest.mark.asyncio
async def test_prepare_headers():
    """Test header preparation."""
    default_headers = {"User-Agent": "TestAgent"}
    toolkit = HttpToolkit(default_headers=default_headers)

    # Test with no additional headers
    headers = toolkit._prepare_headers(None)
    assert headers == default_headers

    # Test with additional headers
    request_headers = {"Authorization": "Bearer token"}
    headers = toolkit._prepare_headers(request_headers)
    assert headers == {"User-Agent": "TestAgent", "Authorization": "Bearer token"}


@pytest.mark.asyncio
async def test_successful_get_request():
    """Test successful GET request."""
    toolkit = HttpToolkit()

    mock_response = MockResponse(
        status_code=200,
        json_data={"id": 1, "name": "test"},
        headers={"content-type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await toolkit.get("https://api.example.com/users/1")

        assert response.status_code == 200
        assert response.json_data == {"id": 1, "name": "test"}
        assert response.is_success is True


@pytest.mark.asyncio
async def test_successful_post_request():
    """Test successful POST request with JSON data."""
    toolkit = HttpToolkit()

    mock_response = MockResponse(
        status_code=201,
        json_data={"id": 1, "name": "created"},
        headers={"content-type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        json_data = {"name": "test user"}
        response = await toolkit.post(
            "https://api.example.com/users", json_data=json_data
        )

        assert response.status_code == 201
        assert response.json_data == {"id": 1, "name": "created"}


@pytest.mark.asyncio
async def test_404_error_handling():
    """Test 404 error handling."""
    toolkit = HttpToolkit()

    mock_response = MockResponse(
        status_code=404, text="Not Found", headers={"content-type": "text/plain"}
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(Exception) as exc_info:
            await toolkit.get("https://api.example.com/users/999")

        error = exc_info.value
        assert "Not Found" in str(error)
        assert "404" in str(error)


@pytest.mark.asyncio
async def test_401_error_handling():
    """Test 401 unauthorized error handling."""
    toolkit = HttpToolkit()

    mock_response = MockResponse(
        status_code=401, text="Unauthorized", headers={"content-type": "text/plain"}
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(Exception) as exc_info:
            await toolkit.get("https://api.example.com/protected")

        error = exc_info.value
        assert "Unauthorized" in str(error)
        assert "authentication" in str(error).lower()


@pytest.mark.asyncio
async def test_timeout_error():
    """Test timeout error handling."""
    toolkit = HttpToolkit()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(Exception) as exc_info:
            await toolkit.get("https://api.example.com/slow")

        error = exc_info.value
        assert "timed out" in str(error).lower()


@pytest.mark.asyncio
async def test_connection_error():
    """Test connection error handling."""
    toolkit = HttpToolkit()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(Exception) as exc_info:
            await toolkit.get("https://api.example.com/unreachable")

        error = exc_info.value
        assert "Connection failed" in str(error)


@pytest.mark.asyncio
async def test_request_validation():
    """Test HttpRequest validation."""
    # Valid request
    request = HttpRequest(url="https://api.example.com/users")
    assert request.url == "https://api.example.com/users"
    assert request.method == "GET"

    # Invalid URL without scheme
    with pytest.raises(ValueError) as exc_info:
        HttpRequest(url="api.example.com/users")
    assert "scheme" in str(exc_info.value)

    # Empty URL
    with pytest.raises(ValueError) as exc_info:
        HttpRequest(url="")
    assert "empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_multiple_data_payloads_error():
    """Test error when multiple data payloads are provided."""
    toolkit = HttpToolkit()

    request = HttpRequest(
        url="https://api.example.com/users",
        method="POST",
        json_data={"name": "test"},
        form_data={"name": "test"},
        content="test content",
    )

    with pytest.raises(Exception) as exc_info:
        await toolkit.request(request)

    error = exc_info.value
    assert "Multiple data payloads" in str(error)


@pytest.mark.asyncio
async def test_response_properties():
    """Test HttpResponse properties."""
    # Success response
    response = HttpResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        content='{"test": true}',
        url="https://api.example.com/test",
        elapsed_ms=100.0,
    )

    assert response.is_success is True
    assert response.is_redirect is False
    assert response.is_client_error is False
    assert response.is_server_error is False

    # Client error response
    error_response = HttpResponse(
        status_code=400,
        headers={},
        content="Bad Request",
        url="https://api.example.com/test",
        elapsed_ms=50.0,
    )

    assert error_response.is_success is False
    assert error_response.is_client_error is True
    assert error_response.is_server_error is False


@pytest.mark.asyncio
async def test_all_http_methods():
    """Test all HTTP methods."""
    toolkit = HttpToolkit()

    mock_response = MockResponse(status_code=200, json_data={"success": True})

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        # Test GET
        response = await toolkit.get("https://api.example.com/test")
        assert response.status_code == 200

        # Test POST
        response = await toolkit.post(
            "https://api.example.com/test", json_data={"test": True}
        )
        assert response.status_code == 200

        # Test PUT
        response = await toolkit.put(
            "https://api.example.com/test", json_data={"test": True}
        )
        assert response.status_code == 200

        # Test PATCH
        response = await toolkit.patch(
            "https://api.example.com/test", json_data={"test": True}
        )
        assert response.status_code == 200

        # Test DELETE
        response = await toolkit.delete("https://api.example.com/test")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_custom_headers_and_timeout():
    """Test custom headers and timeout configuration."""
    toolkit = HttpToolkit(default_headers={"User-Agent": "TestAgent"}, timeout=60.0)

    mock_response = MockResponse(status_code=200)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await toolkit.get(
            "https://api.example.com/test",
            headers={"Authorization": "Bearer token"},
            timeout=120.0,
        )

        # Verify the request was made
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs["timeout"] == 120.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
