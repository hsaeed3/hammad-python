"""hammad-python"""

from __future__ import annotations

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer as __hammad_importer__

if TYPE_CHECKING:
    # hammad.cache
    from .cache import cached, Cache

    # hammad.cli
    from .cli import print, animate, input

    # hammad.data
    from .data.configurations import (
        Configuration,
        read_configuration_from_file,
        read_configuration_from_url,
        read_configuration_from_os_vars,
        read_configuration_from_os_prefix,
        read_configuration_from_dotenv,
    )
    from .data.collections.collection import Collection, create_collection
    from .data.models import (
        Model,
        field,
        validator,
        model_settings,
        convert_to_pydantic_model,
        convert_to_pydantic_field,
    )
    from .data.types import Audio, Image, Text

    # hammad.formatting
    from .formatting.json import convert_to_json_schema
    from .formatting.text import convert_to_text, convert_type_to_text

    # hammad.logging
    from .logging.logger import Logger, create_logger
    from .logging.decorators import trace, trace_cls, trace_function, trace_http

    # hammad.service
    from .service.decorators import (
        serve as serve_function,
        serve_mcp as serve_function_as_mcp,
    )

    # hammad.web
    from .web.http.client import create_http_client
    from .web.openapi.client import create_openapi_client
    from .web.search.client import create_search_client
    from .web.utils import (
        run_web_request,
        read_web_page,
        read_web_pages,
        run_news_search,
        run_web_search,
        extract_web_page_links,
    )


__all__ = [
    # hammad.cache
    "cached",
    "Cache",
    # hammad.cli
    "print",
    "animate",
    "input",
    # hammad.data
    "Configuration",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_vars",
    "read_configuration_from_os_prefix",
    "read_configuration_from_dotenv",
    "Collection",
    "create_collection",
    "Model",
    "field",
    "validator",
    "model_settings",
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "Audio",
    "Image",
    "Text",
    # hammad.formatting
    "convert_to_json_schema",
    "convert_to_text",
    "convert_type_to_text",
    # hammad.logging
    "Logger",
    "create_logger",
    "trace",
    "trace_cls",
    "trace_function",
    "trace_http",
    # hammad.service
    "serve_function",
    "serve_function_as_mcp",
    # hammad.web
    "create_http_client",
    "create_openapi_client",
    "create_search_client",
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "run_web_search",
    "run_news_search",
    "extract_web_page_links",
]


__getattr__ = __hammad_importer__(__all__)


def __dir__() -> list[str]:
    return __all__
