"""
eval-interface.mcp.servers.launcher

Contains quick launcher methods that allow running mcp servers
based on a set of functions and descriptions. This process uses
"subprocess" and ensures that each server is correctly terminated
after the session is complete. This also allows for multiple
servers to be ran in parallel within the same process, even if they
are serving over HTTP ports.
"""

import sys
import socket
import subprocess
import inspect
import signal
import time
import atexit
from dataclasses import dataclass, field
from typing import Callable, List, Literal, Dict, Any

import logging

logger = logging.getLogger(__name__)

__all__ = [
    "MCPServerService",
    "launch_stdio_mcp_server",
    "launch_sse_mcp_server",
    "launch_streamable_http_mcp_server",
    "find_next_free_port",
    "get_server_service",
    "shutdown_all_servers",
]


def find_next_free_port(start_port: int = 8000, host: str = "127.0.0.1") -> int:
    """
    Finds the next free port starting from the given start_port.
    """
    port = start_port
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
            logger.debug(f"Found free port {port} on host {host}.")
            return port
        except OSError:
            port += 1
            if port > 65535:
                logger.error(f"No free ports found above {start_port} on host {host}.")
                raise IOError("No free ports found")


# Global variables for signal handling
_signal_handlers_registered = False


def _register_signal_handlers():
    """Register signal handlers for graceful shutdown."""
    global _signal_handlers_registered
    if _signal_handlers_registered:
        return

    def signal_handler(signum, frame):
        logger.info(
            f"Received signal {signum}. Shutting down all MCP server services..."
        )
        global _singleton_service
        if _singleton_service is not None:
            try:
                _singleton_service.shutdown_all()
            except Exception as e:
                logger.error(f"Error during signal-triggered shutdown: {e}")
        logger.info("Signal-triggered shutdown complete.")

    # Register handlers for common termination signals
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Also register atexit handler as a fallback
    def atexit_handler():
        global _singleton_service
        if _singleton_service is not None:
            _singleton_service.shutdown_all()

    atexit.register(atexit_handler)
    _signal_handlers_registered = True


@dataclass
class MCPServerService:
    """
    Class that manages the lifecycles and startup/shutdown of
    configured MCP servers by running them as subprocesses.
    """

    active_servers: List[subprocess.Popen] = field(default_factory=list)
    python_executable: str = sys.executable
    process_startup_timeout: float = (
        10.0  # seconds to wait for process startup verification
    )

    def __post_init__(self):
        """Register signal handlers when service is created."""
        _register_signal_handlers()

    def _generate_runner_script(
        self,
        name: str,
        instructions: str | None,
        tools_source_code: List[str],
        tool_function_names: List[str],
        dependencies: List[str],
        log_level: str,
        debug_mode: bool,
        transport: Literal["stdio", "sse", "streamable-http"],
        server_settings: Dict[str, Any],
    ) -> str:
        """
        Generates the Python script content that will be run by the subprocess.
        """
        import textwrap

        # Properly dedent and format tool definitions
        formatted_tools = []
        for source in tools_source_code:
            # Remove common leading whitespace to fix indentation
            dedented_source = textwrap.dedent(source)
            formatted_tools.append(dedented_source)

        tool_definitions_str = "\n\n".join(formatted_tools)

        tool_registrations_str = ""
        for func_name in tool_function_names:
            tool_registrations_str += f"    server.add_tool({func_name})\n"

        # Safely represent instructions string, handling None and quotes
        if instructions is None:
            instructions_repr = "None"
        else:
            escaped_instructions = instructions.replace("'''", "'''")
            instructions_repr = f"'''{escaped_instructions}'''"

        script_lines = [
            "import sys",
            "from mcp.server.fastmcp import FastMCP",
            "from typing import Literal, List, Callable, Any, Dict",
            "import anyio",  # FastMCP.run might use it implicitly or explicitly
            "import logging",  # For basic logging within the script if needed
            "",
            "# Set up logger for tool functions",
            "logger = logging.getLogger(__name__)",
            "",
            "# Import dependencies for UCP tool functions",
            "try:",
            "    from eval_interface.ucp.search_client import UCPSearchClient",
            "    from eval_interface.ucp.types import SearchContentItem, KnowledgeBit",
            "except ImportError as e:",
            "    logger.warning(f'Could not import UCP dependencies: {e}')",
            "    UCPSearchClient = None",
            "    SearchContentItem = None",
            "    KnowledgeBit = None",
            "",
            "# --- Tool Function Definitions ---",
            tool_definitions_str,
            "# --- End Tool Function Definitions ---",
            "",
            "def main():",
            "    # Configure basic logging for the runner script itself",
            "    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
            f"    logging.basicConfig(level='{log_level.upper()}', format=log_format)",
            "    script_logger = logging.getLogger('mcp_runner_script')",
            f'    script_logger.info(f"MCP Runner script for {name!r} starting with transport {transport!r}")',
            f"    server_specific_settings = {server_settings!r}",
            f"    server = FastMCP(",
            f"        name={name!r},",
            f"        instructions={instructions_repr},",
            f"        dependencies={dependencies!r},",
            f"        log_level='{log_level.upper()}',",
            f"        debug={debug_mode},",
            "        **server_specific_settings",
            "    )",
            "",
            "    script_logger.info('Registering tools...')",
            tool_registrations_str,
            "    script_logger.info('Tools registered.')",
            "",
            f'    script_logger.info(f"Starting FastMCP server {name!r} with transport {transport!r}...")',
            f"    server.run(transport={transport!r})",  # mount_path for SSE is handled by FastMCP settings
            f'    script_logger.info(f"FastMCP server {name!r} has shut down.")',
            "",
            "if __name__ == '__main__':",
            "    main()",
        ]
        return "\n".join(script_lines)

    def _verify_process_started(self, process: subprocess.Popen, name: str) -> bool:
        """
        Verify that the process started successfully and is running.

        Args:
            process: The subprocess to verify
            name: Name of the server for logging

        Returns:
            True if process started successfully, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < self.process_startup_timeout:
            poll_result = process.poll()

            if poll_result is None:
                # Process is still running - this is good
                logger.debug(f"Server '{name}' (PID {process.pid}) is running")
                return True
            elif poll_result != 0:
                # Process exited with error
                stderr_output = ""
                if process.stderr:
                    try:
                        stderr_output = process.stderr.read()
                    except Exception as e:
                        logger.warning(
                            f"Could not read stderr from failed process: {e}"
                        )
                logger.error(
                    f"Server '{name}' (PID {process.pid}) failed to start. Exit code: {poll_result}. Stderr: {stderr_output}"
                )
                return False

            # Give it a moment before checking again
            time.sleep(0.1)

        # Timeout reached
        if process.poll() is None:
            logger.warning(
                f"Server '{name}' (PID {process.pid}) startup verification timed out after {self.process_startup_timeout}s, but process is still running"
            )
            return True
        else:
            logger.error(
                f"Server '{name}' (PID {process.pid}) failed to start within {self.process_startup_timeout}s"
            )
            return False

    def launch_server_process(
        self,
        name: str,
        instructions: str | None,
        tools: List[Callable],
        dependencies: List[str],
        log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        debug_mode: bool,
        transport: Literal["stdio", "sse", "streamable-http"],
        server_settings: Dict[str, Any],  # host, port etc. for sse/http
        cwd: str | None = None,
    ) -> subprocess.Popen:
        """
        Prepares and launches an MCP server in a subprocess.
        """
        tools_source_code = []
        tool_function_names = []
        for tool_func in tools:
            try:
                # Attempt to get source. This is fragile for complex tools or non-file-based functions.
                source = inspect.getsource(tool_func)
                tools_source_code.append(source)
                tool_function_names.append(tool_func.__name__)
            except (TypeError, OSError) as e:
                logger.error(
                    f"Could not get source for tool '{tool_func.__name__}': {e}. This tool will be SKIPPED."
                )
                continue

        script_content = self._generate_runner_script(
            name=name,
            instructions=instructions,
            tools_source_code=tools_source_code,
            tool_function_names=tool_function_names,
            dependencies=dependencies,
            log_level=log_level,
            debug_mode=debug_mode,
            transport=transport,
            server_settings=server_settings,
        )
        logger.debug(
            f"Generated runner script for server '{name}' ({transport}):\n{script_content}"
        )

        process = None
        try:
            process = subprocess.Popen(
                [self.python_executable, "-c", script_content],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Decode stdout/stderr as text
            )

            logger.info(f"Launched {transport} server '{name}' with PID {process.pid}.")

            # Verify the process started successfully before adding to active_servers
            if self._verify_process_started(process, name):
                self.active_servers.append(process)
                logger.info(
                    f"Server '{name}' (PID {process.pid}) verified as started successfully."
                )
                # TODO: Optionally, start threads here to read process.stdout and process.stderr
                # and log them using eval_interface.common.logger for better visibility.
                return process
            else:
                # Process failed to start properly, clean it up
                logger.error(
                    f"Server '{name}' failed startup verification, cleaning up..."
                )
                self._cleanup_single_process(process, name, force_kill_timeout=2.0)
                raise RuntimeError(f"Server '{name}' failed to start properly")

        except Exception as e:
            logger.critical(f"Failed to launch subprocess for server '{name}': {e}")
            if process and process.poll() is None:
                # If we created a process but had an error, clean it up
                self._cleanup_single_process(process, name, force_kill_timeout=2.0)
            raise

    def _cleanup_single_process(
        self, process: subprocess.Popen, name: str, force_kill_timeout: float = 5.0
    ):
        """
        Clean up a single process with proper error handling.

        Args:
            process: The process to clean up
            name: Name for logging
            force_kill_timeout: How long to wait before force killing
        """
        if process.poll() is not None:
            logger.debug(f"Process '{name}' (PID {process.pid}) already terminated.")
            return

        logger.info(f"Terminating server process '{name}' (PID {process.pid})...")
        try:
            process.terminate()  # Ask nicely first
            try:
                process.wait(
                    timeout=force_kill_timeout
                )  # Wait for graceful termination
                logger.info(
                    f"Server process '{name}' (PID {process.pid}) terminated gracefully."
                )
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Server process '{name}' (PID {process.pid}) did not terminate gracefully after {force_kill_timeout}s, killing."
                )
                process.kill()  # Force kill
                process.wait()  # Ensure it's reaped
                logger.info(f"Server process '{name}' (PID {process.pid}) killed.")
        except Exception as e:
            logger.error(
                f"Error during cleanup of process '{name}' (PID {process.pid}): {e}"
            )

    def get_running_servers(self) -> List[subprocess.Popen]:
        """
        Get a list of currently running server processes.

        Returns:
            List of running Popen objects
        """
        running = []
        for server_process in self.active_servers:
            if server_process.poll() is None:
                running.append(server_process)
        return running

    def cleanup_dead_servers(self):
        """
        Remove dead processes from the active_servers list.
        """
        original_count = len(self.active_servers)
        self.active_servers = [
            server for server in self.active_servers if server.poll() is None
        ]
        cleaned_count = original_count - len(self.active_servers)
        if cleaned_count > 0:
            logger.info(
                f"Cleaned up {cleaned_count} dead server process(es) from active list."
            )

    def shutdown_all(self, force_kill_timeout: float = 5.0):
        """
        Shutdown all managed server processes.

        Args:
            force_kill_timeout: How long to wait before force killing each process
        """
        if not self.active_servers:
            logger.info("No active MCP server services to shut down.")
            return

        logger.info(
            f"Shutting down {len(self.active_servers)} MCP server service(s)..."
        )

        # Create a copy of the list to iterate over, in case of concurrent modifications
        servers_to_shutdown = self.active_servers.copy()

        for server_process in servers_to_shutdown:
            try:
                # Try to extract server name from the process args for better logging
                server_name = "unknown"
                if hasattr(server_process, "args") and len(server_process.args) > 2:
                    # Try to extract name from the script content
                    script_snippet = (
                        server_process.args[2][:50]
                        if server_process.args[2]
                        else "unknown"
                    )
                    server_name = f"script:{script_snippet}..."

                self._cleanup_single_process(
                    server_process, server_name, force_kill_timeout
                )
            except Exception as e:
                logger.error(
                    f"Error shutting down server process (PID {server_process.pid}): {e}"
                )

        self.active_servers = []
        logger.info("All managed MCP server services shut down.")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown_all()


# Global singleton service instance - declared after class definition
_singleton_service: "MCPServerService | None" = None


# ------------------------------------------------------------------------------
# Singleton Server Service Management
# ------------------------------------------------------------------------------


def get_server_service() -> MCPServerService:
    """
    Get the singleton MCPServerService instance.
    Creates one if it doesn't exist.

    Returns:
        The singleton MCPServerService instance
    """
    global _singleton_service
    if _singleton_service is None:
        _singleton_service = MCPServerService()
        logger.debug("Created singleton MCPServerService instance")
    return _singleton_service


def shutdown_all_servers(force_kill_timeout: float = 5.0):
    """
    Shutdown all servers managed by the singleton service.

    Args:
        force_kill_timeout: How long to wait before force killing each process
    """
    global _singleton_service
    if _singleton_service is not None:
        _singleton_service.shutdown_all(force_kill_timeout)


# ------------------------------------------------------------------------------
# Simplified Launch Functions (No Service Manager Required)
# ------------------------------------------------------------------------------


def launch_stdio_mcp_server(
    name: str,
    instructions: str | None = None,
    tools: List[Callable] = None,
    dependencies: List[str] = None,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    debug_mode: bool = False,
    cwd: str | None = None,
) -> subprocess.Popen:
    """
    Quickly launches an MCP server using FastMCP with stdio transport in a subprocess.

    The server is automatically managed by a singleton service instance.

    Args:
        name: Name of the MCP server.
        instructions: Optional instructions for the MCP server.
        tools: List of tool functions to register. (Caveats apply, see MCPServerService).
        dependencies: List of dependencies for FastMCP.
        log_level: Logging level for the server.
        debug_mode: Whether to run FastMCP in debug mode.
        cwd: Optional current working directory for the subprocess.

    Returns:
        The Popen object for the launched subprocess.
    """
    if tools is None:
        tools = []
    if dependencies is None:
        dependencies = []

    logger.info(f"Preparing to launch STDIN/OUT MCP Server: {name}")
    service = get_server_service()
    return service.launch_server_process(
        name=name,
        instructions=instructions,
        tools=tools,
        dependencies=dependencies,
        log_level=log_level,
        debug_mode=debug_mode,
        transport="stdio",
        server_settings={},
        cwd=cwd,
    )


def launch_sse_mcp_server(
    name: str,
    instructions: str | None = None,
    host: str = "127.0.0.1",
    start_port: int = 8000,
    mount_path: str = "/",
    sse_path: str = "/sse",
    message_path: str = "/messages/",
    json_response: bool = False,
    stateless_http: bool = False,
    warn_on_duplicate_resources: bool = True,
    warn_on_duplicate_tools: bool = True,
    tools: List[Callable] = None,
    dependencies: List[str] = None,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    debug_mode: bool = False,
    cwd: str | None = None,
) -> subprocess.Popen:
    """
    Quickly launches an MCP server using FastMCP with SSE transport in a subprocess.
    It will find the next available port starting from `start_port`.

    The server is automatically managed by a singleton service instance.

    Args:
        name: Name of the MCP server.
        instructions: Optional instructions for the MCP server.
        host: Host for the SSE server.
        start_port: Port number to start searching for a free port.
        mount_path: Mount path for the Starlette application in FastMCP.
        sse_path: SSE endpoint path within FastMCP settings.
        message_path: Message endpoint path for SSE, within FastMCP settings.
        warn_on_duplicate_resources: FastMCP setting.
        warn_on_duplicate_tools: FastMCP setting.
        tools: List of tool functions to register. (Caveats apply, see MCPServerService).
        dependencies: List of dependencies for FastMCP.
        log_level: Logging level for the server.
        debug_mode: Whether to run FastMCP in debug mode.
        cwd: Optional current working directory for the subprocess.

    Returns:
        The Popen object for the launched subprocess.
    """
    if tools is None:
        tools = []
    if dependencies is None:
        dependencies = []

    actual_port = find_next_free_port(start_port, host)
    logger.info(f"Preparing to launch SSE MCP Server: {name} on {host}:{actual_port}")

    server_http_settings = {
        "host": host,
        "port": actual_port,
        "mount_path": mount_path,
        "sse_path": sse_path,
        "message_path": message_path,
        "json_response": json_response,
        "stateless_http": stateless_http,
        "warn_on_duplicate_resources": warn_on_duplicate_resources,
        "warn_on_duplicate_tools": warn_on_duplicate_tools,
    }

    service = get_server_service()
    return service.launch_server_process(
        name=name,
        instructions=instructions,
        tools=tools,
        dependencies=dependencies,
        log_level=log_level,
        debug_mode=debug_mode,
        transport="sse",
        server_settings=server_http_settings,
        cwd=cwd,
    )


def launch_streamable_http_mcp_server(
    name: str,
    instructions: str | None = None,
    host: str = "127.0.0.1",
    start_port: int = 8000,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    json_response: bool = False,
    stateless_http: bool = False,
    warn_on_duplicate_resources: bool = True,
    warn_on_duplicate_tools: bool = True,
    tools: List[Callable] = None,
    dependencies: List[str] = None,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    debug_mode: bool = False,
    cwd: str | None = None,
) -> subprocess.Popen:
    """
    Quickly launches an MCP server using FastMCP with StreamableHTTP transport in a subprocess.
    It will find the next available port starting from `start_port`.

    The server is automatically managed by a singleton service instance.

    Args:
        name: Name of the MCP server.
        instructions: Optional instructions for the MCP server.
        host: Host for the StreamableHTTP server.
        start_port: Port number to start searching for a free port.
        mount_path: Mount path for the root Starlette application in FastMCP.
                    The StreamableHTTP endpoint will be relative to this.
        streamable_http_path: The specific path for the StreamableHTTP MCP endpoint.
        json_response: FastMCP setting for StreamableHTTP to send JSON responses.
        stateless_http: FastMCP setting for StreamableHTTP true stateless mode.
        warn_on_duplicate_resources: FastMCP setting.
        warn_on_duplicate_tools: FastMCP setting.
        tools: List of tool functions to register. (Caveats apply, see MCPServerService).
        dependencies: List of dependencies for FastMCP.
        log_level: Logging level for the server.
        debug_mode: Whether to run FastMCP in debug mode.
        cwd: Optional current working directory for the subprocess.

    Returns:
        The Popen object for the launched subprocess.
    """
    if tools is None:
        tools = []
    if dependencies is None:
        dependencies = []

    actual_port = find_next_free_port(start_port, host)
    logger.info(
        f"Preparing to launch StreamableHTTP MCP Server: {name} on {host}:{actual_port}"
    )

    server_http_settings = {
        "host": host,
        "port": actual_port,
        "mount_path": mount_path,
        "streamable_http_path": streamable_http_path,
        "json_response": json_response,
        "stateless_http": stateless_http,
        "warn_on_duplicate_resources": warn_on_duplicate_resources,
        "warn_on_duplicate_tools": warn_on_duplicate_tools,
    }

    service = get_server_service()
    return service.launch_server_process(
        name=name,
        instructions=instructions,
        tools=tools,
        dependencies=dependencies,
        log_level=log_level,
        debug_mode=debug_mode,
        transport="streamable-http",
        server_settings=server_http_settings,
        cwd=cwd,
    )


# Example Usage (optional, for testing this module directly):
if __name__ == "__main__":
    logger.info("MCP Launcher Example")

    # Dummy tool functions for testing
    def example_tool_one(param: str) -> str:
        # This tool relies on NO external imports from its original scope
        return f"Example tool one received: {param}"

    import math  # Test if tool using its own internal import works

    def example_tool_two(num: float) -> str:
        return f"Square root of {num} is {math.sqrt(num)}"

    # Launch servers directly - no need to create service manager!

    # Launch a stdio server
    stdio_server_process = launch_stdio_mcp_server(
        name="MyStdioServer",
        instructions="This is a test stdio server.",
        tools=[example_tool_one, example_tool_two],
        log_level="DEBUG",
        debug_mode=True,
    )

    # Launch an SSE server
    sse_server_process = launch_sse_mcp_server(
        name="MySSEServer",
        instructions="This is a test SSE server.",
        tools=[example_tool_one],
        start_port=8080,
        log_level="DEBUG",
        debug_mode=True,
    )

    # Launch a StreamableHTTP server
    streamable_http_server_process = launch_streamable_http_mcp_server(
        name="MyStreamableHTTPServer",
        instructions="This is a test StreamableHTTP server.",
        tools=[example_tool_two],
        start_port=8090,  # Start search from 8090
        log_level="DEBUG",
        debug_mode=True,
        json_response=True,  # Example of a specific setting
    )

    logger.info(f"Launched Stdio server PID: {stdio_server_process.pid}")
    logger.info(
        f"Launched SSE server PID: {sse_server_process.pid} on some port (check logs)"
    )
    logger.info(
        f"Launched StreamableHTTP server PID: {streamable_http_server_process.pid} on some port (check logs)"
    )

    try:
        # Keep main process alive for a bit to see servers run
        logger.info("Servers running... press Ctrl+C to shut down example.")

        # This is just so the example runs for a moment.
        # Replace with actual application logic.
        for _ in range(10):  # Simulate some work or waiting period
            if (
                stdio_server_process.poll() is not None
                or sse_server_process.poll() is not None
                or streamable_http_server_process.poll() is not None
            ):
                logger.info("A server process has exited.")
                break
            import time  # Ensure time is imported for sleep

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info("Shutting down all example servers...")
        shutdown_all_servers()  # Use the singleton shutdown function
        logger.info("Example finished.")
