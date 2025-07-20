"""hammad.types

Library level reference to nearly all internally defined types within the
`hammad-python` ecosystem.
"""

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer


if TYPE_CHECKING:
    # ! Cache
    from .cache.base_cache import BaseCache, CacheParams, CacheReturn, CacheType
    from .cache.file_cache import FileCacheLocation

    # ! CLI
    from .cli.styles.types import (
        CLIStyleBackgroundType,
        CLIStyleBoxName,
        CLIStyleColorName,
        CLIStyleError,
        CLIStyleJustifyMethod,
        CLIStyleOverflowMethod,
        CLIStyleStyleName,
        CLIStyleType,
        CLIStyleVerticalOverflowMethod,
    )

    # ! DATA
    from .data.sql.database import (
        DatabaseItemType,
        DatabaseItem,
        DatabaseError,
        DatabaseItemFilters,
    )
    from .data.types.file import File, FileSource
    from .data.types.multimodal.audio import Audio
    from .data.types.multimodal.image import (
        Image,
    )
    from .data.types.text import (
        Text,
        SimpleText,
        CodeSection,
        SchemaSection,
        OutputFormat,
        OutputText,
    )
    from .data.configurations import Configuration

    # ! GENAI
    from .genai.types.base import (
        BaseGenAIModel,
        BaseGenAIModelEvent,
        BaseGenAIModelResponse,
        BaseGenAIModelSettings,
        BaseGenAIModelStream,
    )
    from .genai.types.history import History
    from .genai.types.tools import Tool, BaseTool, ToolResponseMessage
    from .genai.agents.types.agent_context import AgentContext
    from .genai.agents.types.agent_event import AgentEvent
    from .genai.agents.types.agent_hooks import HookManager, HookDecorator
    from .genai.agents.types.agent_messages import AgentMessages
    from .genai.agents.types.agent_response import AgentResponse
    from .genai.agents.types.agent_stream import AgentStream, AgentResponseChunk
    from .genai.graphs.types import (
        GraphContext,
        GraphEnd,
        GraphEvent,
        GraphHistoryEntry,
        GraphResponse,
        GraphNode,
        GraphResponseChunk,
        GraphRunContext,
        GraphStream,
        GraphState,
        BaseGraph,
        PydanticGraphContext,
    )
    from .genai.models.embeddings.types.embedding_model_name import EmbeddingModelName
    from .genai.models.embeddings.types.embedding_model_response import (
        EmbeddingModelResponse,
    )
    from .genai.models.embeddings.types.embedding_model_run_params import (
        EmbeddingModelRunParams,
    )
    from .genai.models.language.types.language_model_instructor_mode import (
        LanguageModelInstructorMode,
    )
    from .genai.models.language.types.language_model_name import LanguageModelName
    from .genai.models.language.types.language_model_messages import (
        LanguageModelMessages,
    )
    from .genai.models.language.types.language_model_response import (
        LanguageModelResponse,
    )
    from .genai.models.language.types.language_model_response_chunk import (
        LanguageModelResponseChunk,
    )
    from .genai.models.language.types.language_model_request import LanguageModelRequest
    from .genai.models.language.types.language_model_response import (
        LanguageModelResponse,
    )
    from .genai.models.language.types.language_model_response_chunk import (
        LanguageModelResponseChunk,
    )
    from .genai.models.language.types.language_model_stream import LanguageModelStream
    from .genai.models.language.types.language_model_settings import (
        LanguageModelSettings,
    )

    # ! LOGGING
    from .logging.logger import (
        LoggerLevelSettings,
        LoggerLevelName,
        FileConfig,
        LoggerConfig,
    )

    # ! MCP
    from .mcp import (
        MCPClientSseSettings,
        MCPClientStdioSettings,
        MCPClientStreamableHttpSettings,
        MCPServerSseSettings,
        MCPServerStdioSettings,
        MCPServerStreamableHttpSettings,
    )

    # ! SERVICE
    from .service.create import (
        ServiceConfig,
        ServiceStatus,
    )
    from .service.decorators import ServiceFunctionParams, ServiceFunctionReturn

    # ! WEB
    from .web.models import (
        SearchResult,
        NewsResult,
        SearchResults,
        NewsResults,
        LinkInfo,
        ImageInfo,
        SelectedElement,
        WebPageResult,
        WebPageErrorResult,
        ExtractedLink,
        HttpResponse,
        WebPageResults,
    )
    from .web.http.client import (
        HttpError,
        HttpRequest,
        HttpResponse,
    )
    from .web.openapi.client import (
        OpenAPIError,
        ParameterInfo,
        RequestBodyInfo,
        ResponseInfo,
        OpenAPIOperation,
        OpenAPISpec,
    )


__all__ = (
    # ! Cache
    "BaseCache",
    "CacheParams",
    "CacheReturn",
    "CacheType",
    "FileCacheLocation",
    # ! CLI
    "CLIStyleBackgroundType",
    "CLIStyleBoxName",
    "CLIStyleColorName",
    "CLIStyleError",
    "CLIStyleJustifyMethod",
    "CLIStyleOverflowMethod",
    "CLIStyleStyleName",
    "CLIStyleType",
    "CLIStyleVerticalOverflowMethod",
    # ! DATA
    "DatabaseItemType",
    "DatabaseItem",
    "DatabaseError",
    "DatabaseItemFilters",
    "File",
    "FileSource",
    "Audio",
    "Image",
    "Text",
    "SimpleText",
    "CodeSection",
    "SchemaSection",
    "OutputFormat",
    "OutputText",
    "Configuration",
    # ! GENAI
    "BaseGenAIModel",
    "BaseGenAIModelEvent",
    "BaseGenAIModelResponse",
    "BaseGenAIModelSettings",
    "BaseGenAIModelStream",
    "History",
    "Tool",
    "BaseTool",
    "ToolResponseMessage",
    "AgentContext",
    "AgentEvent",
    "HookManager",
    "HookDecorator",
    "AgentMessages",
    "AgentResponse",
    "AgentStream",
    "AgentResponseChunk",
    "GraphContext",
    "GraphEnd",
    "GraphEvent",
    "GraphHistoryEntry",
    "GraphResponse",
    "GraphNode",
    "GraphResponseChunk",
    "GraphRunContext",
    "GraphStream",
    "GraphState",
    "BaseGraph",
    "PydanticGraphContext",
    "EmbeddingModelName",
    "EmbeddingModelResponse",
    "EmbeddingModelRunParams",
    "LanguageModelInstructorMode",
    "LanguageModelName",
    "LanguageModelMessages",
    "LanguageModelResponse",
    "LanguageModelResponseChunk",
    "LanguageModelRequest",
    "LanguageModelStream",
    "LanguageModelSettings",
    # ! LOGGING
    "LoggerLevelSettings",
    "LoggerLevelName",
    "FileConfig",
    "LoggerConfig",
    # ! MCP
    "MCPClientSseSettings",
    "MCPClientStdioSettings",
    "MCPClientStreamableHttpSettings",
    "MCPServerSseSettings",
    "MCPServerStdioSettings",
    "MCPServerStreamableHttpSettings",
    # ! SERVICE
    "ServiceConfig",
    "ServiceStatus",
    "ServiceFunctionParams",
    "ServiceFunctionReturn",
    # ! WEB
    "SearchResult",
    "NewsResult",
    "SearchResults",
    "NewsResults",
    "LinkInfo",
    "ImageInfo",
    "SelectedElement",
    "WebPageResult",
    "WebPageErrorResult",
    "ExtractedLink",
    "HttpResponse",
    "WebPageResults",
    "HttpError",
    "HttpRequest",
    "OpenAPIError",
    "ParameterInfo",
    "RequestBodyInfo",
    "ResponseInfo",
    "OpenAPIOperation",
    "OpenAPISpec",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the types module."""
    return list(__all__)
