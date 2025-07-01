"""
Tests for MCP server services.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch

from hammad.mcp.servers.launcher import (
    MCPServerService,
    launch_stdio_mcp_server,
    launch_sse_mcp_server,
    launch_streamable_http_mcp_server,
    find_next_free_port,
    get_server_service,
    shutdown_all_servers,
)


class TestFindNextFreePort:
    """Test cases for find_next_free_port function."""

    def test_find_free_port_default(self):
        """Test finding a free port with default parameters."""
        port = find_next_free_port()
        assert isinstance(port, int)
        assert port >= 8000
        assert port <= 65535

    def test_find_free_port_custom_start(self):
        """Test finding a free port with custom start port."""
        port = find_next_free_port(start_port=9000)
        assert isinstance(port, int)
        assert port >= 9000
        assert port <= 65535

    def test_find_free_port_custom_host(self):
        """Test finding a free port with custom host."""
        port = find_next_free_port(host="localhost")
        assert isinstance(port, int)
        assert port >= 8000
        assert port <= 65535

    @patch("socket.socket")
    def test_find_free_port_socket_error(self, mock_socket):
        """Test handling socket errors when finding ports."""
        mock_socket_instance = Mock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # First few attempts fail, then succeed
        mock_socket_instance.bind.side_effect = [OSError(), OSError(), None]

        port = find_next_free_port(start_port=8000)
        assert port == 8002  # Should succeed on third attempt

    @patch("socket.socket")
    def test_find_free_port_no_ports_available(self, mock_socket):
        """Test when no ports are available."""
        mock_socket_instance = Mock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.side_effect = OSError()

        with pytest.raises(IOError, match="No free ports found"):
            find_next_free_port(start_port=65530)  # Start near the end


class TestMCPServerService:
    """Test cases for MCPServerService class."""

    def test_init_default(self):
        """Test default initialization."""
        service = MCPServerService()
        assert service.active_servers == []
        assert service.python_executable is not None
        assert service.process_startup_timeout == 10.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        service = MCPServerService(
            active_servers=[],
            python_executable="/usr/bin/python3",
            process_startup_timeout=15.0,
        )
        assert service.python_executable == "/usr/bin/python3"
        assert service.process_startup_timeout == 15.0

    def test_generate_runner_script_basic(self):
        """Test generating basic runner script."""
        service = MCPServerService()

        def dummy_tool(param: str) -> str:
            return f"Result: {param}"

        script = service._generate_runner_script(
            name="test_server",
            instructions="Test instructions",
            tools_source_code=[
                "def dummy_tool(param: str) -> str:\n    return f'Result: {param}'"
            ],
            tool_function_names=["dummy_tool"],
            dependencies=["requests"],
            log_level="INFO",
            debug_mode=False,
            transport="stdio",
            server_settings={},
        )

        assert "test_server" in script
        assert "Test instructions" in script
        assert "dummy_tool" in script
        assert "requests" in script
        assert "stdio" in script
        assert "INFO" in script

    def test_generate_runner_script_with_none_instructions(self):
        """Test generating runner script with None instructions."""
        service = MCPServerService()

        script = service._generate_runner_script(
            name="test_server",
            instructions=None,
            tools_source_code=["def dummy_tool(): pass"],
            tool_function_names=["dummy_tool"],
            dependencies=[],
            log_level="DEBUG",
            debug_mode=True,
            transport="sse",
            server_settings={"host": "localhost", "port": 8080},
        )

        assert "instructions=None" in script
        assert "DEBUG" in script
        assert "debug=True" in script
        assert "sse" in script

    def test_verify_process_started_success(self):
        """Test successful process verification."""
        service = MCPServerService()
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.pid = 12345

        result = service._verify_process_started(mock_process, "test_server")

        assert result is True

    def test_verify_process_started_failure(self):
        """Test process verification when process fails."""
        service = MCPServerService()
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.pid = 12345
        mock_process.stderr = Mock()
        mock_process.stderr.read.return_value = "Error output"

        result = service._verify_process_started(mock_process, "test_server")

        assert result is False

    @patch("time.sleep")
    def test_verify_process_started_timeout(self, mock_sleep):
        """Test process verification timeout."""
        service = MCPServerService()
        service.process_startup_timeout = 0.1  # Very short timeout

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.pid = 12345

        # Mock time.time to simulate timeout, but provide enough values for logging
        with patch("time.time") as mock_time:
            mock_time.side_effect = [
                0,
                0.2,
                0.3,
                0.4,
                0.5,
            ]  # Extra values for logging calls

            result = service._verify_process_started(mock_process, "test_server")

            assert result is True  # Should still return True if process is running

    def test_cleanup_single_process_already_terminated(self):
        """Test cleanup of already terminated process."""
        service = MCPServerService()
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Already terminated
        mock_process.pid = 12345

        service._cleanup_single_process(mock_process, "test_server")

        mock_process.terminate.assert_not_called()

    def test_cleanup_single_process_graceful_termination(self):
        """Test graceful process termination."""
        service = MCPServerService()
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.pid = 12345
        mock_process.wait.return_value = None  # Graceful termination

        service._cleanup_single_process(
            mock_process, "test_server", force_kill_timeout=1.0
        )

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=1.0)
        mock_process.kill.assert_not_called()

    def test_cleanup_single_process_forced_kill(self):
        """Test forced process termination."""
        service = MCPServerService()
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.pid = 12345
        mock_process.wait.side_effect = subprocess.TimeoutExpired("test", 1.0)

        service._cleanup_single_process(
            mock_process, "test_server", force_kill_timeout=1.0
        )

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_get_running_servers(self):
        """Test getting list of running servers."""
        service = MCPServerService()

        # Mock processes - one running, one terminated
        running_process = Mock()
        running_process.poll.return_value = None  # Running

        terminated_process = Mock()
        terminated_process.poll.return_value = 0  # Terminated

        service.active_servers = [running_process, terminated_process]

        running_servers = service.get_running_servers()

        assert len(running_servers) == 1
        assert running_servers[0] == running_process

    def test_cleanup_dead_servers(self):
        """Test cleanup of dead servers from active list."""
        service = MCPServerService()

        # Mock processes - one running, one terminated
        running_process = Mock()
        running_process.poll.return_value = None  # Running

        terminated_process = Mock()
        terminated_process.poll.return_value = 0  # Terminated

        service.active_servers = [running_process, terminated_process]

        service.cleanup_dead_servers()

        assert len(service.active_servers) == 1
        assert service.active_servers[0] == running_process

    def test_shutdown_all_no_servers(self):
        """Test shutdown when no servers are active."""
        service = MCPServerService()
        service.active_servers = []

        service.shutdown_all()

        assert service.active_servers == []

    def test_shutdown_all_with_servers(self):
        """Test shutdown with active servers."""
        service = MCPServerService()

        mock_process1 = Mock()
        mock_process1.pid = 12345
        mock_process1.args = ["python", "-c", "test script content"]
        mock_process2 = Mock()
        mock_process2.pid = 67890
        mock_process2.args = ["python", "-c", "another script"]

        service.active_servers = [mock_process1, mock_process2]

        with patch.object(service, "_cleanup_single_process") as mock_cleanup:
            service.shutdown_all()

            assert mock_cleanup.call_count == 2
            assert service.active_servers == []

    def test_context_manager(self):
        """Test context manager functionality."""
        with patch.object(MCPServerService, "shutdown_all") as mock_shutdown:
            with MCPServerService() as service:
                assert isinstance(service, MCPServerService)

            mock_shutdown.assert_called_once()

    @patch("subprocess.Popen")
    @patch("inspect.getsource")
    def test_launch_server_process_success(self, mock_getsource, mock_popen):
        """Test successful server process launch."""
        service = MCPServerService()

        # Mock tool function
        def dummy_tool():
            pass

        mock_getsource.return_value = "def dummy_tool():\n    pass"

        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(service, "_verify_process_started", return_value=True):
            result = service.launch_server_process(
                name="test_server",
                instructions="Test instructions",
                tools=[dummy_tool],
                dependencies=[],
                log_level="INFO",
                debug_mode=False,
                transport="stdio",
                server_settings={},
            )

            assert result == mock_process
            assert mock_process in service.active_servers
            mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    @patch("inspect.getsource")
    def test_launch_server_process_verification_failure(
        self, mock_getsource, mock_popen
    ):
        """Test server process launch with verification failure."""
        service = MCPServerService()

        def dummy_tool():
            pass

        mock_getsource.return_value = "def dummy_tool():\n    pass"

        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(service, "_verify_process_started", return_value=False):
            with patch.object(service, "_cleanup_single_process") as mock_cleanup:
                with pytest.raises(RuntimeError, match="failed to start properly"):
                    service.launch_server_process(
                        name="test_server",
                        instructions="Test instructions",
                        tools=[dummy_tool],
                        dependencies=[],
                        log_level="INFO",
                        debug_mode=False,
                        transport="stdio",
                        server_settings={},
                    )

                mock_cleanup.assert_called_once()

    @patch("subprocess.Popen")
    @patch("inspect.getsource")
    def test_launch_server_process_with_source_error(self, mock_getsource, mock_popen):
        """Test server process launch when tool source cannot be obtained."""
        service = MCPServerService()

        def dummy_tool():
            pass

        mock_getsource.side_effect = OSError("Source not available")

        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(service, "_verify_process_started", return_value=True):
            result = service.launch_server_process(
                name="test_server",
                instructions="Test instructions",
                tools=[dummy_tool],  # This tool will be skipped
                dependencies=[],
                log_level="INFO",
                debug_mode=False,
                transport="stdio",
                server_settings={},
            )

            assert result == mock_process
            # Should still succeed even if tool source fails


class TestLaunchFunctions:
    """Test cases for launch convenience functions."""

    @patch("hammad.mcp.servers.launcher.get_server_service")
    def test_launch_stdio_mcp_server(self, mock_get_service):
        """Test launch_stdio_mcp_server function."""
        mock_service = Mock()
        mock_process = Mock()
        mock_service.launch_server_process.return_value = mock_process
        mock_get_service.return_value = mock_service

        def dummy_tool():
            pass

        result = launch_stdio_mcp_server(
            name="test_server",
            instructions="Test instructions",
            tools=[dummy_tool],
            dependencies=["requests"],
            log_level="DEBUG",
            debug_mode=True,
            cwd="/tmp",
        )

        assert result == mock_process
        mock_service.launch_server_process.assert_called_once_with(
            name="test_server",
            instructions="Test instructions",
            tools=[dummy_tool],
            dependencies=["requests"],
            log_level="DEBUG",
            debug_mode=True,
            transport="stdio",
            server_settings={},
            cwd="/tmp",
        )

    @patch("hammad.mcp.servers.launcher.get_server_service")
    @patch("hammad.mcp.servers.launcher.find_next_free_port")
    def test_launch_sse_mcp_server(self, mock_find_port, mock_get_service):
        """Test launch_sse_mcp_server function."""
        mock_service = Mock()
        mock_process = Mock()
        mock_service.launch_server_process.return_value = mock_process
        mock_get_service.return_value = mock_service
        mock_find_port.return_value = 8080

        result = launch_sse_mcp_server(
            name="test_server",
            instructions="Test instructions",
            host="localhost",
            start_port=8000,
            tools=[],
            dependencies=[],
            log_level="INFO",
            debug_mode=False,
        )

        assert result == mock_process
        mock_find_port.assert_called_once_with(8000, "localhost")
        mock_service.launch_server_process.assert_called_once()

        # Check that server_settings contains expected values
        call_args = mock_service.launch_server_process.call_args
        server_settings = call_args[1]["server_settings"]
        assert server_settings["host"] == "localhost"
        assert server_settings["port"] == 8080
        assert call_args[1]["transport"] == "sse"

    @patch("hammad.mcp.servers.launcher.get_server_service")
    @patch("hammad.mcp.servers.launcher.find_next_free_port")
    def test_launch_streamable_http_mcp_server(self, mock_find_port, mock_get_service):
        """Test launch_streamable_http_mcp_server function."""
        mock_service = Mock()
        mock_process = Mock()
        mock_service.launch_server_process.return_value = mock_process
        mock_get_service.return_value = mock_service
        mock_find_port.return_value = 9000

        result = launch_streamable_http_mcp_server(
            name="test_server",
            instructions="Test instructions",
            host="0.0.0.0",
            start_port=8000,
            tools=[],
            dependencies=[],
            log_level="ERROR",
            debug_mode=True,
        )

        assert result == mock_process
        mock_find_port.assert_called_once_with(8000, "0.0.0.0")
        mock_service.launch_server_process.assert_called_once()

        # Check that server_settings contains expected values
        call_args = mock_service.launch_server_process.call_args
        server_settings = call_args[1]["server_settings"]
        assert server_settings["host"] == "0.0.0.0"
        assert server_settings["port"] == 9000
        assert call_args[1]["transport"] == "streamable-http"


class TestSingletonService:
    """Test cases for singleton service management."""

    def test_get_server_service_creates_singleton(self):
        """Test that get_server_service creates and returns singleton."""
        # Clear any existing singleton
        import hammad.mcp.servers.launcher as launcher_module

        launcher_module._singleton_service = None

        service1 = get_server_service()
        service2 = get_server_service()

        assert service1 is service2
        assert isinstance(service1, MCPServerService)

    def test_shutdown_all_servers_with_singleton(self):
        """Test shutdown_all_servers function with singleton."""
        import hammad.mcp.servers.launcher as launcher_module

        mock_service = Mock()
        launcher_module._singleton_service = mock_service

        shutdown_all_servers(force_kill_timeout=10.0)

        mock_service.shutdown_all.assert_called_once_with(10.0)

    def test_shutdown_all_servers_no_singleton(self):
        """Test shutdown_all_servers function when no singleton exists."""
        import hammad.mcp.servers.launcher as launcher_module

        launcher_module._singleton_service = None

        # Should not raise an error
        shutdown_all_servers()


class TestSignalHandling:
    """Test cases for signal handling functionality."""

    @patch("signal.signal")
    @patch("atexit.register")
    def test_signal_handlers_registration(self, mock_atexit, mock_signal):
        """Test that signal handlers are registered correctly."""
        # Import the module to trigger registration
        import hammad.mcp.servers.launcher as launcher_module

        # Reset the registration flag
        launcher_module._signal_handlers_registered = False

        # Create a service to trigger registration
        service = MCPServerService()

        # Check that signal handlers were registered
        assert mock_signal.call_count >= 2  # At least SIGTERM and SIGINT
        mock_atexit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-vs"])
