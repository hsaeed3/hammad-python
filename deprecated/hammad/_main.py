"""hammad._main"""


class to:
    """Namespace for converters that can be used to convert objects to various formats.

    The `to` class provides a collection of converters that can be used to convert objects
    to various formats, such as pydantic models, text, markdown, json, and more.
    """

    # ! CONVERTERS
    from .data import (
        convert_to_pydantic_field as pydantic_field,
        convert_to_pydantic_model as pydantic_model,
    )
    from .data.types import (
        convert_to_base_text as text,
        convert_to_simple_text as simple_text,
        convert_to_code_section as code_section,
        convert_to_schema_section as schema_section,
        convert_to_output_instructions as output_instructions,
    )
    from .formatting.json import (
        convert_to_json_schema as json_schema,
    )
    from .formatting.text import (
        convert_to_text as markdown,
    )


class fn:
    """Namespace for decorators that can be used to modify functions, methods, and classes.

    The `fn` class provides a collection of decorators that can be used to modify functions,
    methods, and classes in various ways, such as caching results, tracing function calls,
    and validating input parameters.
    """

    # ! DECORATORS
    from .cache import cached, auto_cached
    from .logging import trace, trace_cls, trace_function, trace_http
    from .data.models import validator
    from .runtime import (
        sequentialize_function as sequentialize,
        parallelize_function as parallelize,
        run_with_retry as retry,
    )
    from .service import serve, serve_mcp


class new:
    """Namespace for factory functions that create new objects, models, services, and clients.

    The `new` class provides convenient access to a variety of factory functions for creating
    commonly used objects in the hammad ecosystem, such as caches, collections, databases,
    models, loggers, agents, services, and web clients.

    Example usage:
        cache = new.cache(...)
        collection = new.collection(...)
        model = new.model(...)
        logger = new.logger(...)
        agent = new.agent(...)
        service = new.service(...)
        http_client = new.http_client(...)
    """

    # ! FACTORIES
    from .cache import (
        create_cache as cache,
    )
    from .data import (
        create_collection as collection,
        create_database as database,
        create_model as model,
    )
    from .logging import create_logger as logger
    from .genai import (
        create_agent as agent,
        create_embedding_model as embedding_model,
        create_language_model as language_model,
    )
    from .service import (
        create_service as service,
        async_create_service as async_service,
    )
    from .mcp import (
        MCPClient as mcp_client,
    )
    from .web import (
        create_http_client as http_client,
        create_openapi_client as openapi_client,
        create_search_client as search_client,
    )


class run:
    """Centeral namespace for 'one-off' runners, or functions that can be
    executed directly, and standalone."""

    # ! RUNNERS
    from .genai import (
        run_agent as agent,
        run_agent_iter as agent_iter,
        run_embedding_model as embedding_model,
        run_image_edit_model as image_edit_model,
        run_image_generation_model as image_generation_model,
        run_image_variation_model as image_variation_model,
        run_language_model as language_model,
        run_reranking_model as reranking_model,
        run_transcription_model as transcription_model,
        run_tts_model as text_to_speech_model,
    )
    from .mcp import (
        launch_mcp_servers as mcp_servers,
    )
    from .web import (
        run_news_search as news_search,
        run_web_search as web_search,
        run_web_request as web_request,
    )


class read:
    """Namespace for various resource, URL or other file-type readers."""

    from .data.configurations import (
        read_configuration_from_dotenv as configuration_from_dotenv,
        read_configuration_from_file as configuration_from_file,
        read_configuration_from_url as configuration_from_url,
        read_configuration_from_os_prefix as configuration_from_os_prefix,
        read_configuration_from_os_vars as configuration_from_os_vars,
    )
    from .data.types import (
        read_file_from_bytes as file_from_bytes,
        read_file_from_path as file_from_path,
        read_file_from_url as file_from_url,
        read_audio_from_path as audio_from_path,
        read_audio_from_url as audio_from_url,
        read_image_from_path as image_from_path,
        read_image_from_url as image_from_url,
    )
    from .web import (
        read_web_page as web_page,
        read_web_pages as web_pages,
        extract_web_page_links as extract_links,
    )


class settings:
    """Namespace class for all settings definitions within the ecosystem. This is an
    easy way to find the configuration settings for the component you are intending
    to use."""

    # NOTE:
    # these are attached to the 'core/builtin' extensions imported at the very top
    # hence the weird very very literal names
    from .cli import (
        CLIStyleLiveSettings as live,
        CLIStyleBackgroundSettings as bg,
        CLIStyleRenderableSettings as style,
    )

    from .data import (
        QdrantCollectionIndexSettings as qdrant,
        QdrantCollectionIndexQuerySettings as qdrant_query,
        TantivyCollectionIndexSettings as tantivy,
        TantivyCollectionIndexQuerySettings as tantivy_query,
    )
    from .logging.logger import LoggerLevelSettings as logger_level
    from .genai import (
        AgentSettings as agent,
        LanguageModelSettings as language_model,
        EmbeddingModelSettings as embedding_model,
    )
    from .mcp import (
        MCPClientSseSettings as mcp_client_sse,
        MCPClientStdioSettings as mcp_client_stdio,
        MCPClientStreamableHttpSettings as mcp_client_streamable_http,
        MCPServerSseSettings as mcp_server_sse,
        MCPServerStdioSettings as mcp_server_stdio,
        MCPServerStreamableHttpSettings as mcp_server_streamable_http,
    )


__all__ = (
    # hammad.cache
    "cached",
    # hammad.cli
    "print",
    "input",
    "animate",
    # hammad.logging
    "logger",
    # hammad.genai
    "BaseGraph",
    "plugin",
    "action",
    "agent",
    "llm",
    "tool",
    # hammad.data.collections
    "collection",
    # hammad.formatting.text
    "markdown",
    # hammad.mcp
    "launch_mcp_servers",
    # hammad.service
    "serve",
    "serve_mcp",
    # hammad.web
    "web_search",
    "web_request",
    # hammad.to
    "to",
    # hammad.fn
    "fn",
    # hammad.new
    "new",
    # hammad.run
    "run",
    # hammad.read
    "read",
    # hammad.settings
    "settings",
)
