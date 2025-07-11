"""hammad.mcp.client.client

Contains the `MCPClient` class.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, overload
import threading
import concurrent.futures
import inspect

try:
    from mcp.types import CallToolResult, Tool as MCPTool
    from openai.types.chat.chat_completion_tool_param import (
        ChatCompletionToolParam as OpenAITool,
    )
    from openai.types.shared import FunctionDefinition as Function
except ImportError:
    CallToolResult = Any
    MCPTool = Any
    OpenAITool = Any
    Function = Any

from .client_service import (
    MCPClientService,
    MCPClientServiceSse,
    MCPClientServiceStdio,
    MCPClientServiceStreamableHttp,
)
from .settings import (
    MCPClientSettings,
)

__all__ = (
    "MCPClient",
    "MCPToolWrapper",
    "convert_mcp_tool_to_openai_tool",
)


# -----------------------------------------------------------------------------
# Client
# -----------------------------------------------------------------------------


def convert_mcp_tool_to_openai_tool(mcp_tool: MCPTool) -> OpenAITool:
    return OpenAITool(
        type="function",
        function=Function(
            name=mcp_tool.name,
            description=mcp_tool.description,
            parameters=mcp_tool.inputSchema if mcp_tool.inputSchema else {},
        ),
    )


@dataclass
class MCPToolWrapper:
    """
    Wrapper class that provides a runnable method and tool definitions
    for an MCP tool.
    """

    server_name: str
    tool_name: str
    tool_description: str
    tool_args: dict[str, Any]
    mcp_tool: MCPTool
    openai_tool: OpenAITool
    function: Callable[..., Any]


@dataclass
class MCPClient:
    """
    High-level interface for connecting to MCP servers using different transports.

    This class provides both synchronous and asynchronous methods for interacting
    with MCP servers, wrapping the lower-level client service implementations.
    """

    client_service: MCPClientService
    _connected: bool = False
    _sync_loop: asyncio.AbstractEventLoop = field(default=None, init=False)
    _sync_thread: threading.Thread = field(default=None, init=False)
    _executor: concurrent.futures.ThreadPoolExecutor = field(default=None, init=False)

    @classmethod
    def from_settings(
        cls,
        settings: MCPClientSettings,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ) -> MCPClient:
        """Create an MCPClient from a settings object.

        Args:
            settings: The MCP client settings object.
            cache_tools_list: Whether to cache the tools list.
            name: A readable name for the client.
            client_session_timeout_seconds: The read timeout for the MCP ClientSession.

        Returns:
            An MCPClient instance.
        """
        if settings.type == "stdio":
            client_service = MCPClientServiceStdio(
                settings=settings.settings,
                cache_tools_list=cache_tools_list,
                name=name,
                client_session_timeout_seconds=client_session_timeout_seconds,
            )
        elif settings.type == "sse":
            client_service = MCPClientServiceSse(
                settings=settings.settings,
                cache_tools_list=cache_tools_list,
                name=name,
                client_session_timeout_seconds=client_session_timeout_seconds,
            )
        elif settings.type == "streamable_http":
            client_service = MCPClientServiceStreamableHttp(
                settings=settings.settings,
                cache_tools_list=cache_tools_list,
                name=name,
                client_session_timeout_seconds=client_session_timeout_seconds,
            )
        else:
            raise ValueError(f"Unsupported client type: {settings.type}")

        return cls(client_service=client_service)

    @classmethod
    def stdio(
        cls,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        encoding: str | None = None,
        encoding_error_handler: Literal["strict", "ignore", "replace"] | None = None,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ) -> MCPClient:
        """Create an MCPClient using the stdio transport.

        Args:
            command: The executable to run to start the server.
            args: Command line args to pass to the executable.
            env: The environment variables to set for the server.
            cwd: The working directory to use when spawning the process.
            encoding: The text encoding used when sending/receiving messages.
            encoding_error_handler: The text encoding error handler.
            cache_tools_list: Whether to cache the tools list.
            name: A readable name for the client.
            client_session_timeout_seconds: The read timeout for the MCP ClientSession.

        Returns:
            An MCPClient instance.
        """
        settings = MCPClientSettings.stdio(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
            encoding=encoding,
            encoding_error_handler=encoding_error_handler,
        )

        return cls.from_settings(
            settings=settings,
            cache_tools_list=cache_tools_list,
            name=name,
            client_session_timeout_seconds=client_session_timeout_seconds,
        )

    @classmethod
    def sse(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        sse_read_timeout: float | None = None,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ) -> MCPClient:
        """Create an MCPClient using the SSE transport.

        Args:
            url: The URL to connect to the server.
            headers: The HTTP headers to send with the request.
            timeout: The timeout for the request in seconds.
            sse_read_timeout: The timeout for the SSE event reads in seconds.
            cache_tools_list: Whether to cache the tools list.
            name: A readable name for the client.
            client_session_timeout_seconds: The read timeout for the MCP ClientSession.

        Returns:
            An MCPClient instance.
        """
        settings = MCPClientSettings.sse(
            url=url,
            headers=headers,
            timeout=timeout,
            sse_read_timeout=sse_read_timeout,
        )

        return cls.from_settings(
            settings=settings,
            cache_tools_list=cache_tools_list,
            name=name,
            client_session_timeout_seconds=client_session_timeout_seconds,
        )

    @classmethod
    def streamable_http(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        sse_read_timeout: float | None = None,
        terminate_on_close: bool | None = None,
        cache_tools_list: bool = False,
        name: str | None = None,
        client_session_timeout_seconds: float | None = 5,
    ) -> MCPClient:
        """Create an MCPClient using the streamable HTTP transport.

        Args:
            url: The URL to connect to the server.
            headers: The HTTP headers to send with the request.
            timeout: The timeout for the request in seconds.
            sse_read_timeout: The timeout for the SSE event reads in seconds.
            terminate_on_close: Whether to terminate the connection on close.
            cache_tools_list: Whether to cache the tools list.
            name: A readable name for the client.
            client_session_timeout_seconds: The read timeout for the MCP ClientSession.

        Returns:
            An MCPClient instance.
        """
        settings = MCPClientSettings.streamable_http(
            url=url,
            headers=headers,
            timeout=timeout,
            sse_read_timeout=sse_read_timeout,
            terminate_on_close=terminate_on_close,
        )

        return cls.from_settings(
            settings=settings,
            cache_tools_list=cache_tools_list,
            name=name,
            client_session_timeout_seconds=client_session_timeout_seconds,
        )

    @property
    def name(self) -> str:
        """A readable name for the client."""
        return self.client_service.name

    def _ensure_sync_context(self):
        """Ensure we have a persistent async context for sync operations."""
        if self._sync_loop is None or self._sync_loop.is_closed():
            self._create_sync_context()

    def _create_sync_context(self):
        """Create a persistent async context for sync operations."""
        if self._executor:
            self._executor.shutdown(wait=False)

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._sync_loop = loop
            try:
                loop.run_forever()
            finally:
                # Clean up when the loop stops
                try:
                    if self._connected:
                        loop.run_until_complete(self.async_cleanup())
                except Exception:
                    pass  # Ignore cleanup errors
                loop.close()

        self._sync_thread = threading.Thread(target=run_loop, daemon=True)
        self._sync_thread.start()

        # Wait for the loop to be ready
        import time

        timeout = 5.0
        start_time = time.time()
        while (self._sync_loop is None or not self._sync_loop.is_running()) and (
            time.time() - start_time
        ) < timeout:
            time.sleep(0.01)

        if self._sync_loop is None or not self._sync_loop.is_running():
            raise RuntimeError("Failed to start sync event loop")

    def _run_in_sync_context(self, coro):
        """Run a coroutine in the persistent sync context."""
        self._ensure_sync_context()

        future = asyncio.run_coroutine_threadsafe(coro, self._sync_loop)
        return future.result()

    def connect(self) -> None:
        """Connect to the MCP server synchronously."""
        self._run_in_sync_context(self.async_connect())

    async def async_connect(self) -> None:
        """Connect to the MCP server asynchronously."""
        if self._connected:
            return
        await self.client_service.connect()
        self._connected = True

    def cleanup(self) -> None:
        """Cleanup the client connection synchronously."""
        try:
            if self._connected:
                self._run_in_sync_context(self.async_cleanup())
        finally:
            # Clean up the sync context
            if self._sync_loop and not self._sync_loop.is_closed():
                self._sync_loop.call_soon_threadsafe(self._sync_loop.stop)
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
            self._sync_loop = None
            self._sync_thread = None

    async def async_cleanup(self) -> None:
        """Cleanup the client connection asynchronously."""
        if not self._connected:
            return
        await self.client_service.cleanup()
        self._connected = False

    def list_tools(self) -> list[MCPTool]:
        """List the tools available on the server synchronously.

        Returns:
            A list of available MCP tools.
        """
        return self._run_in_sync_context(self.async_list_tools())

    def list_wrapped_tools(self) -> list[MCPToolWrapper]:
        """List the tools available on the server as wrapped tools with OpenAI compatibility.

        Returns:
            A list of MCPToolWrapper objects that include both MCP and OpenAI tool formats,
            plus callable functions for each tool.
        """
        # Get the raw MCP tools
        mcp_tools = self.list_tools()

        wrapped_tools = []
        for mcp_tool in mcp_tools:
            # Convert to OpenAI tool format
            openai_tool = convert_mcp_tool_to_openai_tool(mcp_tool)

            # Create a callable function for this tool
            def create_tool_function(tool_name: str):
                def tool_function(**kwargs) -> Any:
                    """Dynamically created function that calls the MCP tool."""
                    return self.call_tool(tool_name, kwargs if kwargs else None)

                # Set function metadata
                tool_function.__name__ = tool_name
                tool_function.__doc__ = f"MCP tool: {mcp_tool.description}"

                return tool_function

            # Extract tool arguments from input schema
            tool_args = {}
            if mcp_tool.inputSchema and isinstance(mcp_tool.inputSchema, dict):
                properties = mcp_tool.inputSchema.get("properties", {})
                for prop_name, prop_info in properties.items():
                    if isinstance(prop_info, dict):
                        tool_args[prop_name] = prop_info.get("type", "any")
                    else:
                        tool_args[prop_name] = "any"

            # Create the wrapper
            wrapper = MCPToolWrapper(
                server_name=self.name,
                tool_name=mcp_tool.name,
                tool_description=mcp_tool.description or "",
                tool_args=tool_args,
                mcp_tool=mcp_tool,
                openai_tool=openai_tool,
                function=create_tool_function(mcp_tool.name),
            )

            wrapped_tools.append(wrapper)

        return wrapped_tools

    async def async_list_tools(self) -> list[MCPTool]:
        """List the tools available on the server asynchronously.

        Returns:
            A list of available MCP tools.
        """
        if not self._connected:
            await self.async_connect()
        return await self.client_service.list_tools()

    def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        """Invoke a tool on the server synchronously.

        Args:
            tool_name: The name of the tool to call.
            arguments: The arguments to pass to the tool.

        Returns:
            The result of the tool call.
        """
        return self._run_in_sync_context(self.async_call_tool(tool_name, arguments))

    async def async_call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        """Invoke a tool on the server asynchronously.

        Args:
            tool_name: The name of the tool to call.
            arguments: The arguments to pass to the tool.

        Returns:
            The result of the tool call.
        """
        if not self._connected:
            await self.async_connect()
        return await self.client_service.call_tool(tool_name, arguments)

    def as_tool(
        self, tool_name: str, func: Callable[..., Any] | None = None
    ) -> Callable[..., Any]:
        """Decorator to convert a function into an MCP tool call.

        This decorator allows you to use a function as if it were a local function,
        but it will actually call the corresponding MCP tool.

        Args:
            tool_name: The name of the MCP tool to call.
            func: The function to decorate (optional, for decorator factory pattern).

        Returns:
            A decorated function that calls the MCP tool.

        Usage:
            @client.as_tool("my_tool")
            def my_function(arg1, arg2):
                pass

            # Or as a factory:
            my_function = client.as_tool("my_tool")
        """

        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args, **kwargs) -> Any:
                # Get the function signature to map arguments properly
                sig = inspect.signature(f)
                parameters = list(sig.parameters.keys())

                # Create a dictionary mapping positional args to parameter names
                arguments = {}

                # Map positional arguments to parameter names
                for i, arg in enumerate(args):
                    if i < len(parameters):
                        arguments[parameters[i]] = arg
                    else:
                        # If there are more positional args than parameters, use generic names
                        arguments[f"arg_{i}"] = arg

                # Add keyword arguments (these override positional if there's a conflict)
                arguments.update(kwargs)

                # Call the MCP tool
                result = self.call_tool(tool_name, arguments if arguments else None)
                return result

            return wrapper

        if func is None:
            # Used as @client.as_tool("tool_name")
            return decorator
        else:
            # Used as @client.as_tool("tool_name", func)
            return decorator(func)

    def __enter__(self) -> MCPClient:
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()

    async def __aenter__(self) -> MCPClient:
        """Async context manager entry."""
        await self.async_connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.async_cleanup()


# -----------------------------------------------------------------------------
# Factory Function
# -----------------------------------------------------------------------------


@overload
def create_mcp_client(
    type: Literal["stdio"],
    *,
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | str | None = None,
    timeout: float = 30.0,
) -> MCPClient:
    """Create an MCP client with stdio transport."""
    ...


@overload
def create_mcp_client(
    type: Literal["sse"],
    *,
    url: str,
    timeout: float = 30.0,
) -> MCPClient:
    """Create an MCP client with SSE transport."""
    ...


@overload
def create_mcp_client(
    type: Literal["http"],
    *,
    url: str,
    timeout: float = 30.0,
) -> MCPClient:
    """Create an MCP client with HTTP transport."""
    ...


def create_mcp_client(
    type: Literal["stdio", "sse", "http"],
    *,
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | str | None = None,
    url: str | None = None,
    timeout: float = 30.0,
) -> MCPClient:
    """Create an MCP client with the specified transport type.

    Args:
        service_type: The type of transport to use ("stdio", "sse", or "http").
        command: Command to run for stdio transport.
        args: Arguments for the command (stdio only).
        env: Environment variables for the command (stdio only).
        cwd: Working directory for the command (stdio only).
        url: URL for SSE or HTTP transport.
        timeout: Connection timeout in seconds.

    Returns:
        A configured MCPClient instance.

    Raises:
        ValueError: If required parameters for the transport type are missing.
    """
    service_type = type

    if service_type == "stdio":
        if command is None:
            raise ValueError("command is required for stdio transport")

        service = MCPClientServiceStdio(
            command=command,
            args=args or [],
            env=env or {},
            cwd=Path(cwd) if cwd else None,
        )

    elif service_type == "sse":
        if url is None:
            raise ValueError("url is required for SSE transport")

        service = MCPClientServiceSse(url=url)

    elif service_type == "http":
        if url is None:
            raise ValueError("url is required for HTTP transport")

        service = MCPClientServiceStreamableHttp(url=url)

    else:
        raise ValueError(f"Unsupported service_type: {service_type}")

    settings = MCPClientSettings(timeout=timeout)
    return MCPClient(service=service, settings=settings)
