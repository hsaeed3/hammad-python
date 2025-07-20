"""ham

```markdown
## `hammad-python`

Fun bunch of stuff ***:)***

This module is a collection over various sub-packages that
define the `ham` namespace. These packages include:

- `hammad-python-core`
- `hammad-python-data`
- `hammad-python-genai`
- `hammad-python-http`
```

You can access a variety of the primary resources from these modules
directly from this top level module.
"""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from .core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    try:
        # ham.core
        from ham.core._internal._logging import set_debug, set_verbose
        from ham.core.cache import cached, auto_cached
        from ham.core.cli import print, animate, input, log, log_iterable, log_progress
        from ham.core.conversion import (
            convert_to_text,
            convert_to_json_schema,
            convert_to_model,
            convert_to_pydantic_model,
        )
        from ham.core.logging import get_logger, trace, trace_http

        # ham.data
        from ham.data.collections import (
            create_collection,
        )

        # ham.genai
        from ham.genai.models.embeddings import run_embedding_model
        from ham.genai.models.language import run_language_model
        from ham.genai.models.reranking import run_reranking_model
        from ham.genai.models.multimodal import (
            run_image_generation_model,
            run_transcription_model,
            run_tts_model,
        )
        from ham.genai.agents import create_agent, run_agent, run_agent_iter
        from ham.genai.graphs import (
            # NOTE: lol... uh i just really wanted everything to be lowercase..
            # this may need a once over
            BaseGraph as basegraph,
            action as graphaction,
        )
        from ham.genai.prompted import (
            prompted_fn as prompted,
            contextualize,
            itemize,
            select,
            tool,
        )
        from ham.genai.a2a import as_a2a_app

        # ham.http
        from ham.http import (
            create_client,
            create_openapi_client,
            create_http_client,
            create_mcp_client,
            create_server,
            create_fast_service,
            function_server,
            function_mcp_server,
            run_web_request,
            read_web_page,
            read_web_pages,
            run_web_search,
            run_news_search,
            extract_web_page_links,
            create_search_client,
        )
    except ImportError:
        from ham.core._internal import (  # type: ignore
            set_debug,
            set_verbose,
        )
        from ham.data import (  # type: ignore
            create_collection,
        )
        from ham.genai import (  # type: ignore
            create_agent,
            run_agent,
            run_agent_iter,
            run_embedding_model,
            run_language_model,
            run_reranking_model,
            run_image_generation_model,
            run_transcription_model,
            run_tts_model,
            basegraph,
            graphaction,
            prompted,
            contextualize,
            itemize,
            select,
            tool,
        )
        from ham.http import (  # type: ignore
            create_client,
            create_openapi_client,
            create_http_client,
            create_mcp_client,
            create_server,
            create_fast_service,
            function_server,
            function_mcp_server,
            run_web_request,
            read_web_page,
            read_web_pages,
            run_web_search,
            run_news_search,
            extract_web_page_links,
            create_search_client,
        )


__all__ = (
    # ham.core
    "set_debug",
    "set_verbose",
    "cached",
    "auto_cached",
    "print",
    "animate",
    "input",
    "log",
    "log_iterable",
    "log_progress",
    "convert_to_text",
    "convert_to_json_schema",
    "convert_to_model",
    "convert_to_pydantic_model",
    "get_logger",
    "trace",
    "trace_http",
    # ham.data
    "create_collection",
    # ham.genai
    "create_agent",
    "run_agent",
    "run_agent_iter",
    "run_embedding_model",
    "run_language_model",
    "run_reranking_model",
    "run_image_generation_model",
    "run_transcription_model",
    "run_tts_model",
    "basegraph",
    "graphaction",
    "prompted",
    "contextualize",
    "itemize",
    "select",
    "tool",
    # ham.http
    "create_client",
    "create_openapi_client",
    "create_http_client",
    "create_mcp_client",
    "create_server",
    "create_fast_service",
    "function_server",
    "function_mcp_server",
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "run_web_search",
    "run_news_search",
    "extract_web_page_links",
    "create_search_client",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad module."""
    return __all__
