"""hammad.mcp.client.client_service

Contains the `MCPClientService` class. (Ported from
OpenAI-Agents)
"""

from __future__ import annotations

import abc
import asyncio
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

try:
    from mcp import ClientSession, StdioServerParameters, Tool as MCPTool, stdio_client
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import GetSessionIdCallback, streamablehttp_client
    from mcp.shared.message import SessionMessage
    from mcp.types import CallToolResult, InitializeResult
except ImportError:
    MCPTool = Any
    ClientSession = Any
    StdioServerParameters = Any
    stdio_client = Any
    sse_client = Any
    GetSessionIdCallback = Any
    streamablehttp_client = Any
    SessionMessage = Any
    CallToolResult = Any
    InitializeResult = Any

import logging

logger = logging.getLogger(__name__)

from .settings import (
    MCPClientStdioSettings,
    MCPClientSseSettings,
    MCPClientStreamableHttpSettings,
)


__all__ = (
    "MCPClientService",
    "MCPClientServiceStdio",
    "MCPClientServiceSse",
    "MCPClientServiceStreamableHttp",
    "UserError",
)


class UserError(Exception):
    """Exception raised when the user makes an error."""

    pass


class MCPClientService(abc.ABC):
    """Base class for Model Context Protocol client services."""

    @abc.abstractmethod
    async def connect(self):
        """Connect to the server. For example, this might mean spawning a subprocess or
        opening a network connection. The server is expected to remain connected until
        `cleanup()` is called.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """A readable name for the client service."""
        pass

    @abc.abstractmethod
    async def cleanup(self):
        """Cleanup the client service. For example, this might mean closing a subprocess or
        closing a network connection.
        """
        pass

    @abc.abstractmethod
    async def list_tools(self) -> list[MCPTool]:
        """List the tools available on the server."""
        pass

    @abc.abstractmethod
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None
    ) -> CallToolResult:
        """Invoke a tool on the server."""
        pass


class _MCPClientServiceWithClientSession(MCPClientService, abc.ABC):
    """Base class for MCP client services that use a `ClientSession` to communicate with the server."""

    def __init__(
        self, cache_tools_list: bool, client_session_timeout_seconds: float | None
    ):
        """
        Args:
            cache_tools_list: Whether to cache the tools list. If `True`, the tools list will be
            cached and only fetched from the server once. If `False`, the tools list will be
            fetched from the server on each call to `list_tools()`. The cache can be invalidated
            by calling `invalidate_tools_cache()`. You should set this to `True` if you know the
            server will not change its tools list, because it can drastically improve latency
            (by avoiding a round-trip to the server every time).

            client_session_timeout_seconds: the read timeout passed to the MCP ClientSession.
        """
        self.session: ClientSession | None = None
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.cache_tools_list = cache_tools_list
        self.server_initialize_result: InitializeResult | None = None

        self.client_session_timeout_seconds = client_session_timeout_seconds

        # The cache is always dirty at startup, so that we fetch tools at least once
        self._cache_dirty = True
        self._tools_list: list[MCPTool] | None = None

    @abc.abstractmethod
    def create_streams(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
            GetSessionIdCallback | None,
        ]
    ]:
        """Create the streams for the server."""
        pass

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.cleanup()

    def invalidate_tools_cache(self):
        """Invalidate the tools cache."""
        self._cache_dirty = True

    async def connect(self):
        """Connect to the server."""
        try:
            transport = await self.exit_stack.enter_async_context(self.create_streams())
            # streamablehttp_client returns (read, write, get_session_id)
            # sse_client returns (read, write)

            read, write, *_ = transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(
                    read,
                    write,
                    timedelta(seconds=self.client_session_timeout_seconds)
                    if self.client_session_timeout_seconds
                    else None,
                )
            )
            server_result = await session.initialize()
            self.server_initialize_result = server_result
            self.session = session
        except Exception as e:
            logger.error(f"Error initializing MCP server: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> list[MCPTool]:
        """List the tools available on the server."""
        if not self.session:
            raise UserError(
                "Server not initialized. Make sure you call `connect()` first."
            )

        # Return from cache if caching is enabled, we have tools, and the cache is not dirty
        if self.cache_tools_list and not self._cache_dirty and self._tools_list:
            return self._tools_list

        # Reset the cache dirty to False
        self._cache_dirty = False

        # Fetch the tools from the server
        self._tools_list = (await self.session.list_tools()).tools
        return self._tools_list

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None
    ) -> CallToolResult:
        """Invoke a tool on the server."""
        if not self.session:
            raise UserError(
                "Server not initialized. Make sure you call `connect()` first."
            )

        return await self.session.call_tool(tool_name, arguments)

    async def cleanup(self):
        """Cleanup the server."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error cleaning up server: {e}")
            finally:
                self.session = None


class MCPClientServiceStdio(_MCPClientServiceWithClientSession):
    """MCP client service implementation that uses the stdio transport. See the [spec]
    (https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio) for
    details.
    """

    def __init__(
        self,
        settings: MCPClientStdioSettings,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ):
        """Create a new MCP client service based on the stdio transport.

        Args:
            settings: The settings that configure the client service. This includes the command to run to
                start the server, the args to pass to the command, the environment variables to
                set for the server, the working directory to use when spawning the process, and
                the text encoding used when sending/receiving messages to the server.
            cache_tools_list: Whether to cache the tools list. If `True`, the tools list will be
                cached and only fetched from the server once. If `False`, the tools list will be
                fetched from the server on each call to `list_tools()`. The cache can be
                invalidated by calling `invalidate_tools_cache()`. You should set this to `True`
                if you know the server will not change its tools list, because it can drastically
                improve latency (by avoiding a round-trip to the server every time).
            name: A readable name for the client service. If not provided, we'll create one from the
                command.
            client_session_timeout_seconds: the read timeout passed to the MCP ClientSession.
        """
        super().__init__(cache_tools_list, client_session_timeout_seconds)

        self.params = StdioServerParameters(
            command=settings["command"],
            args=settings.get("args", []),
            env=settings.get("env"),
            cwd=settings.get("cwd"),
            encoding=settings.get("encoding", "utf-8"),
            encoding_error_handler=settings.get("encoding_error_handler", "strict"),
        )

        self._name = name or f"stdio: {self.params.command}"

    def create_streams(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
            GetSessionIdCallback | None,
        ]
    ]:
        """Create the streams for the server."""
        return stdio_client(self.params)

    @property
    def name(self) -> str:
        """A readable name for the client service."""
        return self._name


class MCPClientServiceSse(_MCPClientServiceWithClientSession):
    """MCP client service implementation that uses the HTTP with SSE transport. See the [spec]
    (https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse)
    for details.
    """

    def __init__(
        self,
        settings: MCPClientSseSettings,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ):
        """Create a new MCP client service based on the HTTP with SSE transport.

        Args:
            settings: The settings that configure the client service. This includes the URL of the server,
                the headers to send to the server, the timeout for the HTTP request, and the
                timeout for the SSE connection.

            cache_tools_list: Whether to cache the tools list. If `True`, the tools list will be
                cached and only fetched from the server once. If `False`, the tools list will be
                fetched from the server on each call to `list_tools()`. The cache can be
                invalidated by calling `invalidate_tools_cache()`. You should set this to `True`
                if you know the server will not change its tools list, because it can drastically
                improve latency (by avoiding a round-trip to the server every time).

            name: A readable name for the client service. If not provided, we'll create one from the
                URL.

            client_session_timeout_seconds: the read timeout passed to the MCP ClientSession.
        """
        super().__init__(cache_tools_list, client_session_timeout_seconds)

        self.settings = settings
        self._name = name or f"sse: {self.settings['url']}"

    def create_streams(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
            GetSessionIdCallback | None,
        ]
    ]:
        """Create the streams for the server."""
        return sse_client(
            url=self.settings["url"],
            headers=self.settings.get("headers", None),
            timeout=self.settings.get("timeout", 5),
            sse_read_timeout=self.settings.get("sse_read_timeout", 60 * 5),
        )

    @property
    def name(self) -> str:
        """A readable name for the client service."""
        return self._name


class MCPClientServiceStreamableHttp(_MCPClientServiceWithClientSession):
    """MCP client service implementation that uses the Streamable HTTP transport. See the [spec]
    (https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http)
    for details.
    """

    def __init__(
        self,
        settings: MCPClientStreamableHttpSettings,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ):
        """Create a new MCP client service based on the Streamable HTTP transport.

        Args:
            settings: The settings that configure the client service. This includes the URL of the server,
                the headers to send to the server, the timeout for the HTTP request, and the
                timeout for the Streamable HTTP connection and whether we need to
                terminate on close.

            cache_tools_list: Whether to cache the tools list. If `True`, the tools list will be
                cached and only fetched from the server once. If `False`, the tools list will be
                fetched from the server on each call to `list_tools()`. The cache can be
                invalidated by calling `invalidate_tools_cache()`. You should set this to `True`
                if you know the server will not change its tools list, because it can drastically
                improve latency (by avoiding a round-trip to the server every time).

            name: A readable name for the client service. If not provided, we'll create one from the
                URL.

            client_session_timeout_seconds: the read timeout passed to the MCP ClientSession.
        """
        super().__init__(cache_tools_list, client_session_timeout_seconds)

        self.settings = settings
        self._name = name or f"streamable_http: {self.settings['url']}"

    def create_streams(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
            GetSessionIdCallback | None,
        ]
    ]:
        """Create the streams for the server."""
        return streamablehttp_client(
            url=self.settings["url"],
            headers=self.settings.get("headers", None),
            timeout=timedelta(seconds=self.settings.get("timeout", 30)),
            sse_read_timeout=timedelta(
                seconds=self.settings.get("sse_read_timeout", 60 * 5)
            ),
            terminate_on_close=self.settings.get("terminate_on_close", True),
        )

    @property
    def name(self) -> str:
        """A readable name for the client service."""
        return self._name
