"""
Tests for MCP client services.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from hammad.mcp.client.client_service import (
    MCPClientServiceStdio,
    MCPClientServiceSse,
    MCPClientServiceStreamableHttp,
    UserError,
)
from hammad.mcp.client.settings import (
    MCPClientStdioSettings,
    MCPClientSseSettings,
    MCPClientStreamableHttpSettings,
)


class TestMCPClientServiceStdio:
    """Test cases for MCPClientServiceStdio."""

    def test_init_basic(self):
        """Test basic initialization."""
        settings: MCPClientStdioSettings = {
            "command": "python",
            "args": ["-m", "test_server"],
        }

        service = MCPClientServiceStdio(
            settings=settings, cache_tools_list=True, name="test_stdio_client"
        )

        assert service.name == "test_stdio_client"
        assert service.cache_tools_list is True
        assert service.params.command == "python"
        assert service.params.args == ["-m", "test_server"]

    def test_init_with_all_settings(self):
        """Test initialization with all settings."""
        settings: MCPClientStdioSettings = {
            "command": "node",
            "args": ["server.js"],
            "env": {"NODE_ENV": "test"},
            "cwd": "/tmp",
            "encoding": "utf-8",
            "encoding_error_handler": "replace",
        }

        service = MCPClientServiceStdio(
            settings=settings,
            cache_tools_list=False,
            name="node_client",
            client_session_timeout_seconds=10.0,
        )

        assert service.name == "node_client"
        assert service.cache_tools_list is False
        assert service.client_session_timeout_seconds == 10.0
        assert service.params.command == "node"
        assert service.params.args == ["server.js"]
        assert service.params.env == {"NODE_ENV": "test"}
        assert service.params.cwd == "/tmp"
        assert service.params.encoding == "utf-8"
        assert service.params.encoding_error_handler == "replace"

    def test_name_defaults_to_command(self):
        """Test that name defaults to command when not provided."""
        settings: MCPClientStdioSettings = {"command": "my_command"}

        service = MCPClientServiceStdio(settings=settings)

        assert service.name == "stdio: my_command"

    @patch("hammad.mcp.client.client_service.stdio_client")
    def test_create_streams(self, mock_stdio_client):
        """Test create_streams method."""
        settings: MCPClientStdioSettings = {"command": "python"}
        service = MCPClientServiceStdio(settings=settings)

        mock_context = Mock()
        mock_stdio_client.return_value = mock_context

        result = service.create_streams()

        assert result == mock_context
        mock_stdio_client.assert_called_once_with(service.params)


class TestMCPClientServiceSse:
    """Test cases for MCPClientServiceSse."""

    def test_init_basic(self):
        """Test basic initialization."""
        settings: MCPClientSseSettings = {
            "url": "https://example.com/mcp",
        }

        service = MCPClientServiceSse(
            settings=settings, cache_tools_list=True, name="test_sse_client"
        )

        assert service.name == "test_sse_client"
        assert service.cache_tools_list is True
        assert service.settings["url"] == "https://example.com/mcp"

    def test_init_with_all_settings(self):
        """Test initialization with all settings."""
        settings: MCPClientSseSettings = {
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer token"},
            "timeout": 30.0,
            "sse_read_timeout": 300.0,
        }

        service = MCPClientServiceSse(
            settings=settings,
            cache_tools_list=False,
            name="sse_client",
            client_session_timeout_seconds=15.0,
        )

        assert service.name == "sse_client"
        assert service.cache_tools_list is False
        assert service.client_session_timeout_seconds == 15.0
        assert service.settings["url"] == "https://example.com/mcp"
        assert service.settings["headers"] == {"Authorization": "Bearer token"}
        assert service.settings["timeout"] == 30.0
        assert service.settings["sse_read_timeout"] == 300.0

    def test_name_defaults_to_url(self):
        """Test that name defaults to URL when not provided."""
        settings: MCPClientSseSettings = {"url": "https://example.com/mcp"}

        service = MCPClientServiceSse(settings=settings)

        assert service.name == "sse: https://example.com/mcp"

    @patch("hammad.mcp.client.client_service.sse_client")
    def test_create_streams(self, mock_sse_client):
        """Test create_streams method."""
        settings: MCPClientSseSettings = {
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer token"},
            "timeout": 30.0,
            "sse_read_timeout": 300.0,
        }
        service = MCPClientServiceSse(settings=settings)

        mock_context = Mock()
        mock_sse_client.return_value = mock_context

        result = service.create_streams()

        assert result == mock_context
        mock_sse_client.assert_called_once_with(
            url="https://example.com/mcp",
            headers={"Authorization": "Bearer token"},
            timeout=30.0,
            sse_read_timeout=300.0,
        )


class TestMCPClientServiceStreamableHttp:
    """Test cases for MCPClientServiceStreamableHttp."""

    def test_init_basic(self):
        """Test basic initialization."""
        settings: MCPClientStreamableHttpSettings = {
            "url": "https://example.com/mcp",
        }

        service = MCPClientServiceStreamableHttp(
            settings=settings, cache_tools_list=True, name="test_http_client"
        )

        assert service.name == "test_http_client"
        assert service.cache_tools_list is True
        assert service.settings["url"] == "https://example.com/mcp"

    def test_init_with_all_settings(self):
        """Test initialization with all settings."""
        settings: MCPClientStreamableHttpSettings = {
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer token"},
            "timeout": 60.0,
            "sse_read_timeout": 600.0,
            "terminate_on_close": False,
        }

        service = MCPClientServiceStreamableHttp(
            settings=settings,
            cache_tools_list=False,
            name="http_client",
            client_session_timeout_seconds=20.0,
        )

        assert service.name == "http_client"
        assert service.cache_tools_list is False
        assert service.client_session_timeout_seconds == 20.0
        assert service.settings["url"] == "https://example.com/mcp"
        assert service.settings["headers"] == {"Authorization": "Bearer token"}
        assert service.settings["timeout"] == 60.0
        assert service.settings["sse_read_timeout"] == 600.0
        assert service.settings["terminate_on_close"] is False

    def test_name_defaults_to_url(self):
        """Test that name defaults to URL when not provided."""
        settings: MCPClientStreamableHttpSettings = {"url": "https://example.com/mcp"}

        service = MCPClientServiceStreamableHttp(settings=settings)

        assert service.name == "streamable_http: https://example.com/mcp"

    @patch("hammad.mcp.client.client_service.streamablehttp_client")
    def test_create_streams(self, mock_streamable_client):
        """Test create_streams method."""
        settings: MCPClientStreamableHttpSettings = {
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer token"},
            "timeout": 60.0,
            "sse_read_timeout": 600.0,
            "terminate_on_close": False,
        }
        service = MCPClientServiceStreamableHttp(settings=settings)

        mock_context = Mock()
        mock_streamable_client.return_value = mock_context

        result = service.create_streams()

        assert result == mock_context
        mock_streamable_client.assert_called_once()

        # Check that timedelta objects are used
        call_args = mock_streamable_client.call_args
        assert call_args[1]["url"] == "https://example.com/mcp"
        assert call_args[1]["headers"] == {"Authorization": "Bearer token"}
        assert call_args[1]["terminate_on_close"] is False


class TestMCPClientServiceWithClientSession:
    """Test cases for the base client session functionality."""

    @pytest.fixture
    def mock_client_service(self):
        """Create a mock client service for testing."""
        settings: MCPClientStdioSettings = {"command": "python"}
        service = MCPClientServiceStdio(settings=settings)
        return service

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_client_service):
        """Test successful connection."""
        mock_session = AsyncMock()
        mock_init_result = Mock()
        mock_session.initialize.return_value = mock_init_result

        with patch.object(mock_client_service, "create_streams") as mock_create_streams:
            mock_transport = (Mock(), Mock())
            mock_create_streams.return_value.__aenter__.return_value = mock_transport

            with patch(
                "hammad.ai.mcp.client.client_service.ClientSession"
            ) as mock_client_session_class:
                mock_client_session_class.return_value.__aenter__.return_value = (
                    mock_session
                )

                await mock_client_service.connect()

                assert mock_client_service.session == mock_session
                assert mock_client_service.server_initialize_result == mock_init_result
                mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_client_service):
        """Test connection failure and cleanup."""
        with patch.object(mock_client_service, "create_streams") as mock_create_streams:
            mock_create_streams.side_effect = Exception("Connection failed")

            with patch.object(mock_client_service, "cleanup") as mock_cleanup:
                with pytest.raises(Exception, match="Connection failed"):
                    await mock_client_service.connect()

                mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_no_session(self, mock_client_service):
        """Test list_tools raises error when no session."""
        with pytest.raises(UserError, match="Server not initialized"):
            await mock_client_service.list_tools()

    @pytest.mark.asyncio
    async def test_list_tools_with_cache(self, mock_client_service):
        """Test list_tools with caching enabled."""
        mock_client_service.cache_tools_list = True
        mock_client_service.session = AsyncMock()
        mock_tools = [Mock(), Mock()]

        # First call - should fetch from server
        mock_client_service.session.list_tools.return_value.tools = mock_tools
        result1 = await mock_client_service.list_tools()

        assert result1 == mock_tools
        assert mock_client_service._tools_list == mock_tools
        assert not mock_client_service._cache_dirty

        # Second call - should use cache
        mock_client_service.session.list_tools.reset_mock()
        result2 = await mock_client_service.list_tools()

        assert result2 == mock_tools
        mock_client_service.session.list_tools.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_tools_without_cache(self, mock_client_service):
        """Test list_tools without caching."""
        mock_client_service.cache_tools_list = False
        mock_client_service.session = AsyncMock()
        mock_tools = [Mock(), Mock()]
        mock_client_service.session.list_tools.return_value.tools = mock_tools

        result = await mock_client_service.list_tools()

        assert result == mock_tools
        mock_client_service.session.list_tools.assert_called_once()

    def test_invalidate_tools_cache(self, mock_client_service):
        """Test cache invalidation."""
        mock_client_service.cache_tools_list = True
        mock_client_service._cache_dirty = False

        mock_client_service.invalidate_tools_cache()

        assert mock_client_service._cache_dirty is True

    @pytest.mark.asyncio
    async def test_call_tool_no_session(self, mock_client_service):
        """Test call_tool raises error when no session."""
        with pytest.raises(UserError, match="Server not initialized"):
            await mock_client_service.call_tool("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_client_service):
        """Test successful tool call."""
        mock_client_service.session = AsyncMock()
        mock_result = Mock()
        mock_client_service.session.call_tool.return_value = mock_result

        result = await mock_client_service.call_tool("test_tool", {"arg": "value"})

        assert result == mock_result
        mock_client_service.session.call_tool.assert_called_once_with(
            "test_tool", {"arg": "value"}
        )

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_client_service):
        """Test cleanup method."""
        mock_client_service.session = Mock()

        with patch.object(mock_client_service.exit_stack, "aclose") as mock_aclose:
            await mock_client_service.cleanup()

            mock_aclose.assert_called_once()
            assert mock_client_service.session is None

    @pytest.mark.asyncio
    async def test_cleanup_with_error(self, mock_client_service):
        """Test cleanup handles errors gracefully."""
        mock_client_service.session = Mock()

        with patch.object(mock_client_service.exit_stack, "aclose") as mock_aclose:
            mock_aclose.side_effect = Exception("Cleanup error")

            # Should not raise, just log the error
            await mock_client_service.cleanup()

            assert mock_client_service.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_client_service):
        """Test async context manager functionality."""
        with patch.object(mock_client_service, "connect") as mock_connect:
            with patch.object(mock_client_service, "cleanup") as mock_cleanup:
                async with mock_client_service as service:
                    assert service == mock_client_service
                    mock_connect.assert_called_once()

                mock_cleanup.assert_called_once()


class TestUserError:
    """Test the UserError exception."""

    def test_user_error_creation(self):
        """Test UserError can be created and raised."""
        error = UserError("Test error message")
        assert str(error) == "Test error message"

        with pytest.raises(UserError, match="Test error message"):
            raise error
