"""hammad.mcp.client.settings

Contains settings for the 3 different MCP client
types.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from typing_extensions import TypedDict, Required, NotRequired

__all__ = (
    "MCPClientStdioSettings",
    "MCPClientSseSettings",
    "MCPClientStreamableHttpSettings",
    "MCPClientSettings",
)


class MCPClientStdioSettings(TypedDict, total=False):
    """Settings for the stdio MCP client."""

    command: Required[str]
    """The executable to run to start the server. For example, `python` or `node`."""
    args: NotRequired[list[str]]
    """Command line args to pass to the `command` executable."""
    env: NotRequired[dict[str, str]]
    """The environment variables to set for the server."""
    cwd: NotRequired[str | Path]
    """The working directory to use when spawning the process."""
    encoding: NotRequired[str]
    """The text encoding used when sending/receiving messages. Defaults to `utf-8`."""
    encoding_error_handler: NotRequired[Literal["strict", "ignore", "replace"]]
    """The text encoding error handler. Defaults to `strict`."""


class MCPClientSseSettings(TypedDict, total=False):
    """Settings for the SSE MCP client."""

    url: Required[str]
    """The URL to connect to the server."""
    headers: NotRequired[dict[str, str]]
    """The HTTP headers to send with the request."""
    timeout: NotRequired[float]
    """The timeout for the request in seconds."""
    sse_read_timeout: NotRequired[float]
    """The timeout for the SSE event reads in seconds."""


class MCPClientStreamableHttpSettings(TypedDict, total=False):
    """Settings for the streamable HTTP MCP client."""

    url: Required[str]
    """The URL to connect to the server."""
    headers: NotRequired[dict[str, str]]
    """The HTTP headers to send with the request."""
    timeout: NotRequired[float]
    """The timeout for the request in seconds."""
    sse_read_timeout: NotRequired[float]
    """The timeout for the SSE event reads in seconds."""
    terminate_on_close: NotRequired[bool]
    """Whether to terminate the connection on close."""


MCPClientSettingsType = (
    MCPClientStdioSettings | MCPClientSseSettings | MCPClientStreamableHttpSettings
)
"""Union type of the 3 different MCP client settings types."""


@dataclass
class MCPClientSettings:
    """
    Helper class to define the settings for the 3 different
    MCP server types.

    This object can be used within a `MCPClient` object
    to create a connection to an MCP server.
    """

    type: Literal["stdio", "sse", "streamable_http"]
    """The type of MCP client this object represents."""
    settings: MCPClientSettingsType
    """The settings for the MCP client."""

    @classmethod
    def stdio(
        cls,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        encoding: str | None = None,
        encoding_error_handler: Literal["strict", "ignore", "replace"] | None = None,
    ) -> MCPClientSettings:
        """Create a settings object for a stdio MCP client.

        Args:
            command: The executable to run to start the server. For example, `python` or `node`.
            args: Command line args to pass to the `command` executable.
            env: The environment variables to set for the server.
            cwd: The working directory to use when spawning the process.
            encoding: The text encoding used when sending/receiving messages. Defaults to `utf-8`.
            encoding_error_handler: The text encoding error handler. Defaults to `strict`.
        """
        return cls(
            type="stdio",
            settings={
                "command": command,
                "args": args,
                "env": env,
                "cwd": cwd,
                "encoding": encoding,
                "encoding_error_handler": encoding_error_handler,
            },
        )

    @classmethod
    def sse(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        sse_read_timeout: float | None = None,
    ) -> MCPClientSettings:
        """Create a settings object for an SSE MCP client.

        Args:
            url: The URL to connect to the server.
            headers: The HTTP headers to send with the request.
            timeout: The timeout for the request in seconds.
            sse_read_timeout: The timeout for the SSE event reads in seconds.
        """
        return cls(
            type="sse",
            settings={
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "sse_read_timeout": sse_read_timeout,
            },
        )

    @classmethod
    def streamable_http(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        sse_read_timeout: float | None = None,
        terminate_on_close: bool | None = None,
    ) -> MCPClientSettings:
        """Create a settings object for a streamable HTTP MCP client.

        Args:
            url: The URL to connect to the server.
            headers: The HTTP headers to send with the request.
            timeout: The timeout for the request in seconds.
            sse_read_timeout: The timeout for the SSE event reads in seconds.
            terminate_on_close: Whether to terminate the connection on close.
        """
        return cls(
            type="streamable_http",
            settings={
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "sse_read_timeout": sse_read_timeout,
                "terminate_on_close": terminate_on_close,
            },
        )


__all__ = [
    "MCPClientSettings",
]
