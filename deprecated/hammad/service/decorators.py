"""hammad.service.decorators"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    Union,
    ParamSpec,
    TypeVar,
)


ServiceFunctionParams = ParamSpec("ServiceFunctionParams")
ServiceFunctionReturn = TypeVar("ServiceFunctionReturn")


def serve(
    func: Optional[Callable[ServiceFunctionParams, ServiceFunctionReturn]] = None,
    *,
    # Overrides
    name: Optional[str] = None,
    method: Literal[
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"
    ] = "POST",
    path: str = "/",
    # Server configuration
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "info",
    reload: bool = False,
    workers: int = 1,
    timeout_keep_alive: int = 5,
    access_log: bool = True,
    use_colors: bool = True,
    auto_start: bool = True,
    # FastAPI
    include_in_schema: bool = True,
    dependencies: Optional[List[Callable[..., Any]]] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> Union[Callable[ServiceFunctionParams, ServiceFunctionReturn], Callable]:
    """Decorator to serve a function as a FastAPI endpoint.

    Can be used as a decorator (@serve) or as a function (serve(func)).

    Args:
        func: Function to serve (when used as decorator, this is None initially)
        name: Service name (defaults to function name)
        method: HTTP method to use
        path: API endpoint path
        host: Host to bind to
        port: Port to bind to
        log_level: Uvicorn log level
        reload: Enable auto-reload
        workers: Number of worker processes
        timeout_keep_alive: Keep-alive timeout
        access_log: Enable access logging
        use_colors: Use colored logs
        auto_start: Automatically start the server
        include_in_schema: Include in OpenAPI schema
        dependencies: FastAPI dependencies
        tags: API tags
        description: API description

    Returns:
        The original function (when used as decorator)
    """
    from .create import create_service
    from ..mcp.servers.launcher import find_next_free_port

    def decorator(
        f: Callable[ServiceFunctionParams, ServiceFunctionReturn],
    ) -> Callable[ServiceFunctionParams, ServiceFunctionReturn]:
        # Find next available port if auto_start is True
        actual_port = port
        if auto_start:
            actual_port = find_next_free_port(port, host)

        # Handle dependencies - convert raw functions to FastAPI Depends
        processed_dependencies = None
        if dependencies is not None:
            from fastapi import Depends

            processed_dependencies = [
                Depends(dep) if callable(dep) else dep for dep in dependencies
            ]

        # Store the service configuration on the function
        f._service_config = {
            "name": name or f.__name__,
            "method": method,
            "path": path,
            "host": host,
            "port": actual_port,
            "log_level": log_level,
            "reload": reload,
            "workers": workers,
            "timeout_keep_alive": timeout_keep_alive,
            "access_log": access_log,
            "use_colors": use_colors,
            "auto_start": auto_start,
            "include_in_schema": include_in_schema,
            "dependencies": processed_dependencies,
            "tags": tags,
            "description": description,
        }

        # Create and start the service immediately if auto_start is True
        if auto_start:
            create_service(f, **f._service_config)

        return f

    if func is None:
        # Called as @serve(...)
        return decorator
    else:
        # Called as @serve (without parentheses)
        return decorator(func)


def serve_mcp(
    fn: Optional[Union[Callable, List[Callable]]] = None,
    *,
    # MCP Server configuration
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
    # Server settings (for sse/http transports)
    host: str = "127.0.0.1",
    port: int = 8000,
    mount_path: str = "/",
    sse_path: str = "/sse",
    message_path: str = "/messages/",
    streamable_http_path: str = "/mcp",
    json_response: bool = False,
    stateless_http: bool = False,
    warn_on_duplicate_resources: bool = True,
    warn_on_duplicate_tools: bool = True,
    # FastMCP settings
    dependencies: Optional[List[str]] = None,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    debug_mode: bool = False,
    cwd: Optional[str] = None,
    # Launch settings
    auto_restart: bool = False,
    check_interval: float = 1.0,
    # Function-specific parameters (only when single function)
    single_func_name: Optional[str] = None,
    single_func_description: Optional[str] = None,
) -> Union[Callable, List[Callable]]:
    """Decorator/function to serve functions as MCP server tools.

    Can be used in multiple ways:
    1. As a decorator: @serve_mcp
    2. As a decorator with params: @serve_mcp(name="MyServer")
    3. As a function with single function: serve_mcp(my_func)
    4. As a function with multiple functions: serve_mcp([func1, func2])

    Args:
        fn: Function or list of functions to serve
        name: MCP server name
        instructions: Server instructions
        transport: Transport type (stdio, sse, streamable-http)
        host: Host for HTTP transports
        port: Starting port for HTTP transports
        mount_path: Mount path for HTTP servers
        sse_path: SSE endpoint path
        message_path: Message endpoint path
        streamable_http_path: StreamableHTTP endpoint path
        json_response: Use JSON responses for HTTP
        stateless_http: Use stateless HTTP mode
        warn_on_duplicate_resources: Warn on duplicate resources
        warn_on_duplicate_tools: Warn on duplicate tools
        dependencies: FastMCP dependencies
        log_level: Logging level
        debug_mode: Enable debug mode
        cwd: Working directory
        auto_restart: Automatically restart failed servers
        check_interval: Health check interval in seconds
        single_func_name: Name override for single function
        single_func_description: Description for single function

    Returns:
        Original function(s) unchanged
    """
    from ..mcp.servers.launcher import (
        launch_mcp_servers,
        MCPServerStdioSettings,
        MCPServerSseSettings,
        MCPServerStreamableHttpSettings,
    )

    def _create_server_config(
        tools: List[Callable], server_name: str, server_instructions: Optional[str]
    ):
        """Create the appropriate server configuration based on transport type."""
        base_config = {
            "name": server_name,
            "instructions": server_instructions,
            "tools": tools,
            "dependencies": dependencies or [],
            "log_level": log_level,
            "debug_mode": debug_mode,
            "cwd": cwd,
        }

        if transport == "stdio":
            return MCPServerStdioSettings(**base_config)
        elif transport == "sse":
            return MCPServerSseSettings(
                **base_config,
                host=host,
                start_port=port,
                mount_path=mount_path,
                sse_path=sse_path,
                message_path=message_path,
                json_response=json_response,
                stateless_http=stateless_http,
                warn_on_duplicate_resources=warn_on_duplicate_resources,
                warn_on_duplicate_tools=warn_on_duplicate_tools,
            )
        elif transport == "streamable-http":
            return MCPServerStreamableHttpSettings(
                **base_config,
                host=host,
                start_port=port,
                mount_path=mount_path,
                streamable_http_path=streamable_http_path,
                json_response=json_response,
                stateless_http=stateless_http,
                warn_on_duplicate_resources=warn_on_duplicate_resources,
                warn_on_duplicate_tools=warn_on_duplicate_tools,
            )
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    def _launch_server(server_config):
        """Launch the MCP server with the given configuration."""
        launch_mcp_servers(
            servers=[server_config],
            check_interval=check_interval,
            auto_restart=auto_restart,
        )

    def decorator(f: Callable) -> Callable:
        """Decorator for single function."""
        func_name = single_func_name or name or f.__name__
        func_instructions = single_func_description or instructions or f.__doc__

        # Create server configuration and launch
        server_config = _create_server_config([f], func_name, func_instructions)
        _launch_server(server_config)

        return f

    def handle_multiple_functions(funcs: List[Callable]) -> List[Callable]:
        """Handle multiple functions."""
        server_name = name or "MCPServer"
        server_instructions = instructions or f"MCP server with {len(funcs)} tools"

        # Create server configuration and launch
        server_config = _create_server_config(funcs, server_name, server_instructions)
        _launch_server(server_config)

        return funcs

    # Handle different call patterns
    if fn is None:
        # Called as @serve_mcp(...) - return decorator
        return decorator
    elif callable(fn):
        # Called as @serve_mcp (no parentheses) or serve_mcp(single_func)
        return decorator(fn)
    elif isinstance(fn, list):
        # Called as serve_mcp([func1, func2, ...])
        return handle_multiple_functions(fn)
    else:
        raise TypeError(f"Expected callable or list of callables, got {type(fn)}")
