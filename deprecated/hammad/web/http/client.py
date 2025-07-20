"""hammad.http.client"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Literal, Optional, Union, overload
from urllib.parse import urljoin, urlparse

import httpx
from pydantic import BaseModel, Field, field_validator

__all__ = (
    "HttpError",
    "HttpRequest",
    "HttpResponse",
    "HttpClient",
)


class HttpError(Exception):
    """Custom exception for HTTP toolkit errors with semantic feedback."""

    def __init__(
        self,
        message: str,
        suggestion: str = "",
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

    def get_full_error(self) -> str:
        """Get the full error message with suggestion and context."""
        error_msg = f"HTTP ERROR: {self.message}"
        if self.status_code:
            error_msg += f" (Status: {self.status_code})"
        if self.suggestion:
            error_msg += f"\nSUGGESTION: {self.suggestion}"
        if self.context:
            error_msg += f"\nCONTEXT: {self.context}"
        if self.response_text:
            error_msg += f"\nRESPONSE: {self.response_text[:500]}..."
        return error_msg

    def __str__(self) -> str:
        """Return the full error message when converting to string."""
        return self.get_full_error()


class HttpRequest(BaseModel):
    """Model for HTTP request configuration with semantic parameterization."""

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"] = "GET"
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = Field(None, alias="json")
    form_data: Optional[Dict[str, Any]] = None
    content: Optional[Union[str, bytes]] = None
    timeout: Optional[float] = 30.0
    follow_redirects: bool = True

    # Semantic authentication parameters
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    bearer_token: Optional[str] = None
    basic_auth: Optional[tuple[str, str]] = None
    auth_header: Optional[str] = None  # Custom auth header value

    # Common convenience parameters
    user_agent: Optional[str] = None
    content_type: Optional[str] = None
    accept: Optional[str] = None

    # Advanced options
    retry_attempts: int = 0
    retry_delay: float = 1.0

    def get_effective_headers(self) -> Dict[str, str]:
        """Get the effective headers with semantic parameters applied."""
        effective_headers = (self.headers or {}).copy()

        # Apply semantic authentication
        if self.api_key:
            effective_headers[self.api_key_header] = self.api_key

        if self.bearer_token:
            effective_headers["Authorization"] = f"Bearer {self.bearer_token}"

        if self.basic_auth:
            import base64

            credentials = base64.b64encode(
                f"{self.basic_auth[0]}:{self.basic_auth[1]}".encode()
            ).decode()
            effective_headers["Authorization"] = f"Basic {credentials}"

        if self.auth_header:
            effective_headers["Authorization"] = self.auth_header

        # Apply convenience headers
        if self.user_agent:
            effective_headers["User-Agent"] = self.user_agent

        if self.content_type:
            effective_headers["Content-Type"] = self.content_type

        if self.accept:
            effective_headers["Accept"] = self.accept

        return effective_headers

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")

        parsed = urlparse(v)
        if not parsed.scheme:
            raise ValueError("URL must include scheme (http:// or https://)")
        if not parsed.netloc:
            raise ValueError("URL must include domain")

        return v.strip()

    @field_validator("method", mode="before")
    @classmethod
    def validate_method(cls, v):
        """Validate HTTP method."""
        return v.upper()


class HttpResponse(BaseModel):
    """Model for HTTP response data."""

    status_code: int
    headers: Dict[str, str]
    content: Union[str, bytes]
    json_data: Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]] = None
    url: str
    elapsed_ms: float

    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status)."""
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        """Check if response is a redirect (3xx status)."""
        return 300 <= self.status_code < 400

    @property
    def is_client_error(self) -> bool:
        """Check if response is a client error (4xx status)."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response is a server error (5xx status)."""
        return 500 <= self.status_code < 600


class AsyncHttpClient:
    """
    Base HTTP toolkit for making HTTP requests with clean type hints and semantic error handling.

    This class provides a clean, well-typed interface for HTTP operations using httpx.
    It includes semantic error handling and validation to provide meaningful feedback.
    """

    def __init__(
        self,
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
    ):
        """
        Initialize the HTTP toolkit.

        Args:
            base_url: Base URL for all requests (optional)
            default_headers: Default headers to include in all requests
            timeout: Default timeout in seconds
            follow_redirects: Whether to follow redirects by default
            verify_ssl: Whether to verify SSL certificates
            api_key: API key for authentication
            api_key_header: Header name for API key (default: X-API-Key)
            bearer_token: Bearer token for Authorization header
            basic_auth: Tuple of (username, password) for basic auth
            user_agent: User-Agent header value
        """
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl

        # Store semantic authentication parameters
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.bearer_token = bearer_token
        self.basic_auth = basic_auth
        self.user_agent = user_agent

        # Apply semantic parameters to default headers
        self._apply_semantic_headers()

        # Validate base_url if provided
        if self.base_url:
            parsed = urlparse(self.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise HttpError(
                    message=f"Invalid base URL: {self.base_url}",
                    suggestion="Provide a valid base URL with scheme and domain (e.g., https://api.example.com)",
                    context={"provided_base_url": self.base_url},
                )

    def _apply_semantic_headers(self) -> None:
        """Apply semantic authentication parameters to default headers."""
        # API Key authentication
        if self.api_key:
            self.default_headers[self.api_key_header] = self.api_key

        # Bearer token authentication
        if self.bearer_token:
            self.default_headers["Authorization"] = f"Bearer {self.bearer_token}"

        # Basic authentication
        if self.basic_auth:
            import base64

            credentials = base64.b64encode(
                f"{self.basic_auth[0]}:{self.basic_auth[1]}".encode()
            ).decode()
            self.default_headers["Authorization"] = f"Basic {credentials}"

        # User-Agent
        if self.user_agent:
            self.default_headers["User-Agent"] = self.user_agent

    def _build_url(self, url: str) -> str:
        """Build the complete URL, combining base_url if provided."""
        if self.base_url:
            return urljoin(self.base_url.rstrip("/") + "/", url.lstrip("/"))
        return url

    def _prepare_headers(
        self, request_or_headers: Union[HttpRequest, Dict[str, str], None]
    ) -> Dict[str, str]:
        """Prepare headers by combining default headers with request-specific ones."""
        combined_headers = self.default_headers.copy()

        if request_or_headers is None:
            # No additional headers
            pass
        elif isinstance(request_or_headers, HttpRequest):
            # Get effective headers from the request (includes semantic parameters)
            request_headers = request_or_headers.get_effective_headers()
            combined_headers.update(request_headers)
        elif isinstance(request_or_headers, dict):
            # Backward compatibility: simple dict of headers
            combined_headers.update(request_or_headers)

        return combined_headers

    async def _execute_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        form_data: Optional[Dict[str, Any]],
        content: Optional[Union[str, bytes]],
        request: HttpRequest,
    ) -> HttpResponse:
        """Execute HTTP request with retry logic."""
        import asyncio
        import time

        last_exception = None

        for attempt in range(request.retry_attempts + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=request.timeout or self.timeout,
                    follow_redirects=request.follow_redirects,
                    verify=self.verify_ssl,
                ) as client:
                    # Record start time
                    start_time = time.time()

                    response = await client.request(
                        method=request.method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                        data=form_data,
                        content=content,
                    )

                    # Calculate elapsed time
                    elapsed_ms = (time.time() - start_time) * 1000

                    # Handle response errors
                    self._handle_response_errors(response)

                    # Parse JSON if possible
                    json_response = None
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        try:
                            json_response = response.json()
                        except json.JSONDecodeError:
                            # Not valid JSON, leave as None
                            pass

                    return HttpResponse(
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        content=response.text,
                        json_data=json_response,
                        url=str(response.url),
                        elapsed_ms=elapsed_ms,
                    )

            except (httpx.ConnectError, httpx.TimeoutException, HttpError) as e:
                last_exception = e

                # Don't retry on client errors (4xx) or authentication issues
                if (
                    isinstance(e, HttpError)
                    and e.status_code
                    and 400 <= e.status_code < 500
                ):
                    raise e

                # If this is the last attempt, raise the exception
                if attempt == request.retry_attempts:
                    raise e

                # Wait before retrying
                if request.retry_delay > 0:
                    await asyncio.sleep(
                        request.retry_delay * (attempt + 1)
                    )  # Exponential backoff

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise HttpError(
                message="Request failed after all retry attempts",
                suggestion="Check your network connection and the server status",
                context={"url": url, "retry_attempts": request.retry_attempts},
            )

    def _handle_response_errors(self, response: httpx.Response) -> None:
        """Handle HTTP response errors with semantic feedback."""
        if response.is_success:
            return

        status_code = response.status_code

        # Get response text safely
        try:
            response_text = response.text
        except Exception:
            response_text = "Unable to decode response text"

        # Provide semantic error messages based on status code
        if status_code == 400:
            raise HttpError(
                message="Bad Request - The server cannot process the request",
                suggestion="Check your request parameters, headers, and data format",
                context={"url": str(response.url), "method": response.request.method},
                status_code=status_code,
                response_text=response_text,
            )
        elif status_code == 401:
            raise HttpError(
                message="Unauthorized - Authentication is required",
                suggestion="Provide valid authentication credentials (API key, token, etc.)",
                context={"url": str(response.url)},
                status_code=status_code,
                response_text=response_text,
            )
        elif status_code == 403:
            raise HttpError(
                message="Forbidden - Access is denied",
                suggestion="Check your permissions or API key scope",
                context={"url": str(response.url)},
                status_code=status_code,
                response_text=response_text,
            )
        elif status_code == 404:
            raise HttpError(
                message="Not Found - The requested resource does not exist",
                suggestion="Verify the URL path and any path parameters",
                context={"url": str(response.url)},
                status_code=status_code,
                response_text=response_text,
            )
        elif status_code == 429:
            raise HttpError(
                message="Too Many Requests - Rate limit exceeded",
                suggestion="Reduce request frequency or wait before retrying",
                context={"url": str(response.url)},
                status_code=status_code,
                response_text=response_text,
            )
        elif 400 <= status_code < 500:
            raise HttpError(
                message=f"Client Error ({status_code}) - Request cannot be fulfilled",
                suggestion="Review your request parameters and try again",
                context={"url": str(response.url), "method": response.request.method},
                status_code=status_code,
                response_text=response_text,
            )
        elif 500 <= status_code < 600:
            raise HttpError(
                message=f"Server Error ({status_code}) - Server encountered an error",
                suggestion="The server is experiencing issues. Try again later or contact support",
                context={"url": str(response.url)},
                status_code=status_code,
                response_text=response_text,
            )
        else:
            raise HttpError(
                message=f"HTTP Error ({status_code})",
                suggestion="An unexpected HTTP error occurred",
                context={"url": str(response.url), "method": response.request.method},
                status_code=status_code,
                response_text=response_text,
            )

    async def request(self, request: HttpRequest) -> HttpResponse:
        """
        Make an HTTP request with semantic error handling.

        Args:
            request: HttpRequest configuration object

        Returns:
            HttpResponse object with response data

        Raises:
            HttpError: On request failures with semantic feedback
        """
        try:
            # Build the complete URL
            url = self._build_url(request.url)

            # Prepare headers
            headers = self._prepare_headers(request)

            # Prepare request data
            json_data = request.json_data
            form_data = request.form_data
            content = request.content

            # Validate data payload
            data_count = sum(
                1 for x in [json_data, form_data, content] if x is not None
            )
            if data_count > 1:
                raise HttpError(
                    message="Multiple data payloads provided",
                    suggestion="Provide only one of: json_data, form_data, or content",
                    context={
                        "has_json": json_data is not None,
                        "has_form": form_data is not None,
                        "has_content": content is not None,
                    },
                )

            # Execute the request with retry logic
            return await self._execute_with_retry(
                url, headers, request.params, json_data, form_data, content, request
            )

        except httpx.TimeoutException:
            raise HttpError(
                message="Request timed out",
                suggestion=f"The request took longer than {request.timeout or self.timeout} seconds. Try increasing the timeout or check the server status",
                context={
                    "url": request.url,
                    "timeout": request.timeout or self.timeout,
                },
            )
        except httpx.ConnectError:
            raise HttpError(
                message="Connection failed",
                suggestion="Check the URL and your internet connection. The server might be down",
                context={"url": request.url},
            )
        except HttpError:
            # Re-raise HttpError as-is
            raise
        except httpx.HTTPStatusError as e:
            # This shouldn't happen since we handle status errors above, but just in case
            raise HttpError(
                message=f"HTTP error {e.response.status_code}",
                suggestion="The server returned an error status",
                context={"url": request.url, "status_code": e.response.status_code},
                status_code=e.response.status_code,
            )
        except Exception as e:
            raise HttpError(
                message=f"Unexpected error: {str(e)}",
                suggestion="An unexpected error occurred. Check your request configuration",
                context={"url": request.url, "error_type": type(e).__name__},
            )

    # Convenience methods
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a GET request with semantic parameters."""
        request = HttpRequest(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
            retry_attempts=retry_attempts,
            **kwargs,
        )
        return await self.request(request)

    async def post(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a POST request with semantic parameters."""
        request = HttpRequest(
            method="POST",
            url=url,
            json_data=json_data,
            form_data=form_data,
            headers=headers,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
            retry_attempts=retry_attempts,
            **kwargs,
        )
        return await self.request(request)

    async def put(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a PUT request with semantic parameters."""
        request = HttpRequest(
            method="PUT",
            url=url,
            json_data=json_data,
            form_data=form_data,
            headers=headers,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
            retry_attempts=retry_attempts,
            **kwargs,
        )
        return await self.request(request)

    async def patch(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a PATCH request with semantic parameters."""
        request = HttpRequest(
            method="PATCH",
            url=url,
            json_data=json_data,
            form_data=form_data,
            headers=headers,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
            retry_attempts=retry_attempts,
            **kwargs,
        )
        return await self.request(request)

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a DELETE request with semantic parameters."""
        request = HttpRequest(
            method="DELETE",
            url=url,
            headers=headers,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
            retry_attempts=retry_attempts,
            **kwargs,
        )
        return await self.request(request)


class HttpClient:
    """
    Base HTTP toolkit for making HTTP requests with clean type hints and semantic error handling.

    This class provides a clean, well-typed interface for HTTP operations using httpx.
    It includes semantic error handling and validation to provide meaningful feedback.
    """

    def __init__(
        self,
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
    ):
        """
        Initialize the HttpClient.

        Args:
            base_url: Base URL for all requests
            default_headers: Default headers to include in all requests
            timeout: Default timeout for HTTP requests in seconds
            follow_redirects: Whether to follow HTTP redirects
            verify_ssl: Whether to verify SSL certificates
            api_key: API key for authentication
            api_key_header: Header name for API key
            bearer_token: Bearer token for authentication
            basic_auth: Username and password tuple for basic authentication
            user_agent: User-Agent header for HTTP requests
        """
        self._async_client = AsyncHttpClient(
            base_url=base_url,
            default_headers=default_headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
            basic_auth=basic_auth,
            user_agent=user_agent,
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

    def request(self, request: HttpRequest) -> HttpResponse:
        """
        Make an HTTP request with semantic error handling.

        Args:
            request: HttpRequest configuration object

        Returns:
            HttpResponse object with response data

        Raises:
            HttpError: On request failures with semantic feedback
        """
        return self._run_async(self._async_client.request(request))

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a GET request with semantic parameters."""
        return self._run_async(
            self._async_client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                api_key=api_key,
                bearer_token=bearer_token,
                retry_attempts=retry_attempts,
                **kwargs,
            )
        )

    def post(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a POST request with semantic parameters."""
        return self._run_async(
            self._async_client.post(
                url,
                json_data=json_data,
                form_data=form_data,
                headers=headers,
                timeout=timeout,
                api_key=api_key,
                bearer_token=bearer_token,
                retry_attempts=retry_attempts,
                **kwargs,
            )
        )

    def put(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a PUT request with semantic parameters."""
        return self._run_async(
            self._async_client.put(
                url,
                json_data=json_data,
                form_data=form_data,
                headers=headers,
                timeout=timeout,
                api_key=api_key,
                bearer_token=bearer_token,
                retry_attempts=retry_attempts,
                **kwargs,
            )
        )

    def patch(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a PATCH request with semantic parameters."""
        return self._run_async(
            self._async_client.patch(
                url,
                json_data=json_data,
                form_data=form_data,
                headers=headers,
                timeout=timeout,
                api_key=api_key,
                bearer_token=bearer_token,
                retry_attempts=retry_attempts,
                **kwargs,
            )
        )

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retry_attempts: int = 0,
        **kwargs,
    ) -> HttpResponse:
        """Make a DELETE request with semantic parameters."""
        return self._run_async(
            self._async_client.delete(
                url,
                headers=headers,
                timeout=timeout,
                api_key=api_key,
                bearer_token=bearer_token,
                retry_attempts=retry_attempts,
                **kwargs,
            )
        )


@overload
def create_http_client(
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
    async_client: Literal[True] = ...,
) -> AsyncHttpClient: ...


@overload
def create_http_client(
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
    async_client: Literal[False] = ...,
) -> HttpClient: ...


def create_http_client(
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
    async_client: bool = False,
) -> Union[HttpClient, AsyncHttpClient]:
    """
    Create a new HttpClient instance.

    Args:
        base_url: Base URL for all requests (optional)
        default_headers: Default headers to include in all requests
        timeout: Default timeout in seconds
        follow_redirects: Whether to follow redirects by default
        verify_ssl: Whether to verify SSL certificates
        api_key: API key for authentication
        api_key_header: Header name for API key (default: X-API-Key)
        bearer_token: Bearer token for Authorization header
        basic_auth: Tuple of (username, password) for basic auth
        user_agent: User-Agent header value
    """
    params = locals()
    del params["async_client"]

    if async_client:
        return AsyncHttpClient(**params)
    else:
        return HttpClient(**params)
