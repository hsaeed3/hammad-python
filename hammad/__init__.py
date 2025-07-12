"""hammad-python

A vast ecosystem of ('nightly', dont trust literally any interface to stay the same
for more than a few days) resources, utilities and components for building applications
in Python."""

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer as __hammad_importer__


if TYPE_CHECKING:
    # BUILTINS | hammad.cli
    from .cli import print, input, animate

    # hammad.cache
    from .cache import Cache, create_cache, cached, auto_cached

    # hammad.formatting
    from .formatting.json import convert_to_json_schema
    from .formatting.text import (
        convert_to_text,
        convert_type_to_text,
        convert_docstring_to_text,
    )

    # hammad.data
    from .data.configurations import (
        Configuration,
        read_configuration_from_os_vars,
        read_configuration_from_file,
        read_configuration_from_url,
    )
    from .data.collections import Collection, create_collection
    from .data.sql import (
        Database as SQLDatabase,
        create_database as create_sql_database,
    )
    from .data.models import (
        Model,
        field,
        validator,
        convert_to_pydantic_field,
        convert_to_pydantic_model,
        is_pydantic_model_class,
    )
    from .data.types import Text, BaseText, Audio, Image, File

    # hammad.genai
    from .genai.graphs import (
        BaseGraph,
        GraphResponse,
        GraphStream,
        GraphResponseChunk,
        GraphBuilder,
        action,
        plugin,
    )
    from .genai.agents import (
        Agent,
        AgentResponse,
        AgentResponseChunk,
        AgentStream,
        create_agent,
        run_agent,
        run_agent_iter,
        async_run_agent,
        async_run_agent_iter,
    )
    from .genai.models.embeddings import (
        Embedding,
        EmbeddingModel,
        EmbeddingModelResponse,
        EmbeddingModelSettings,
        create_embedding_model,
        run_embedding_model,
        async_run_embedding_model,
    )
    from .genai.models.language import (
        LanguageModel,
        LanguageModelRequest,
        LanguageModelResponse,
        LanguageModelResponseChunk,
        LanguageModelStream,
        LanguageModelSettings,
        create_language_model,
        run_language_model,
        async_run_language_model,
    )
    from .genai.models.multimodal import (
        run_image_edit_model,
        run_image_generation_model,
        run_image_variation_model,
        run_transcription_model,
        run_tts_model,
        async_run_image_edit_model,
        async_run_image_generation_model,
        async_run_image_variation_model,
        async_run_transcription_model,
        async_run_tts_model,
    )
    from .genai.models.reranking import run_reranking_model, async_run_reranking_model
    from .genai.types.tools import define_tool, Tool
    from .genai.types.history import History

    # hammad.logging
    from .logging import (
        Logger,
        create_logger,
        create_logger_level,
        trace,
        trace_cls,
        trace_function,
        trace_http,
    )

    # hammad.mcp
    from .mcp import (
        MCPClient,
        MCPClientSseSettings,
        MCPClientStdioSettings,
        MCPClientStreamableHttpSettings,
        MCPServerSseSettings,
        MCPServerStdioSettings,
        MCPServerStreamableHttpSettings,
        launch_mcp_servers,
        convert_mcp_tool_to_openai_tool,
    )

    # hammad.runtime
    from .runtime import (
        run_parallel,
        run_sequentially,
        run_with_retry,
        parallelize_function,
        sequentialize_function,
    )

    # hammad.service
    from .service import create_service, async_create_service, serve, serve_mcp

    # hammad.web
    from .web import (
        HttpClient,
        AsyncHttpClient,
        OpenAPIClient,
        AsyncOpenAPIClient,
        SearchClient,
        AsyncSearchClient,
        create_http_client,
        create_openapi_client,
        create_search_client,
        run_web_search,
        run_news_search,
        run_web_request,
        read_web_page,
        read_web_pages,
        extract_web_page_links,
    )


__all__ = (
    # hammad.cli
    "print",
    "input",
    "animate",
    # hammad.cache
    "Cache",
    "create_cache",
    "cached",
    "auto_cached",
    # hammad.formatting
    "convert_to_json_schema",
    "convert_to_text",
    "convert_type_to_text",
    "convert_docstring_to_text",
    # hammad.data
    "Configuration",
    "read_configuration_from_os_vars",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "Collection",
    "create_collection",
    "SQLDatabase",
    "create_sql_database",
    "Model",
    "field",
    "validator",
    "convert_to_pydantic_field",
    "convert_to_pydantic_model",
    "is_pydantic_model_class",
    "Text",
    "BaseText",
    "Audio",
    "Image",
    "File",
    # hammad.genai
    "BaseGraph",
    "GraphResponse",
    "GraphStream",
    "GraphResponseChunk",
    "GraphBuilder",
    "action",
    "plugin",
    # hammad.genai.agents
    "Agent",
    "AgentResponse",
    "AgentResponseChunk",
    "AgentStream",
    "create_agent",
    "run_agent",
    "run_agent_iter",
    "async_run_agent",
    "async_run_agent_iter",
    # hammad.genai.models.embeddings
    "Embedding",
    "EmbeddingModel",
    "EmbeddingModelResponse",
    "EmbeddingModelSettings",
    "create_embedding_model",
    "run_embedding_model",
    "async_run_embedding_model",
    # hammad.genai.models.language
    "LanguageModel",
    "LanguageModelRequest",
    "LanguageModelResponse",
    "LanguageModelResponseChunk",
    "LanguageModelStream",
    "LanguageModelSettings",
    "create_language_model",
    "run_language_model",
    "async_run_language_model",
    # hammad.genai.models.multimodal
    "run_image_edit_model",
    "run_image_generation_model",
    "run_image_variation_model",
    "run_transcription_model",
    "run_tts_model",
    "async_run_image_edit_model",
    "async_run_image_generation_model",
    "async_run_image_variation_model",
    "async_run_transcription_model",
    "async_run_tts_model",
    # hammad.genai.models.reranking
    "run_reranking_model",
    "async_run_reranking_model",
    # hammad.genai.types.tools
    "define_tool",
    "Tool",
    # hammad.genai.types.history
    "History",
    # hammad.logging
    "Logger",
    "create_logger",
    "create_logger_level",
    "trace",
    "trace_cls",
    "trace_function",
    "trace_http",
    # hammad.mcp
    "MCPClient",
    "MCPClientSseSettings",
    "MCPClientStdioSettings",
    "MCPClientStreamableHttpSettings",
    "MCPServerSseSettings",
    "MCPServerStdioSettings",
    "MCPServerStreamableHttpSettings",
    "launch_mcp_servers",
    "convert_mcp_tool_to_openai_tool",
    # hammad.runtime
    "run_parallel",
    "run_sequentially",
    "run_with_retry",
    "parallelize_function",
    "sequentialize_function",
    # hammad.service
    "create_service",
    "async_create_service",
    "serve",
    "serve_mcp",
    # hammad.web
    "HttpClient",
    "AsyncHttpClient",
    "OpenAPIClient",
    "AsyncOpenAPIClient",
    "SearchClient",
    "AsyncSearchClient",
    "create_http_client",
    "create_openapi_client",
    "create_search_client",
    "run_web_search",
    "run_news_search",
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "extract_web_page_links",
)


__getattr__ = __hammad_importer__(__all__)


def __dir__() -> list[str]:
    return list(__all__)
