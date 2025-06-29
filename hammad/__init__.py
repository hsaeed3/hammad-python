"""hammad-python

```markdown
## Happliy Accelerated Micro Modules (for) Application Development
```
"""

from typing import TYPE_CHECKING
from ._core._utils._import_utils import _auto_create_getattr_loader


if TYPE_CHECKING:
    # hammad.ai
    # NOTE:
    # TO USE MODULES FROM THE `hammad.ai` EXTENSION,
    # REQUIRES INSTALLATION OF THE `hammad-python[ai]` PACKAGE.
    from .ai import (
        create_completion,
        async_create_completion,
        create_embeddings,
        async_create_embeddings,
    )

    # hammad.base
    from .base import Model, field, create_model, is_field, is_model, validator

    # hammad.cache
    from .cache import Cache, cached, auto_cached, create_cache

    # hammad.cli
    from .cli import print, animate, input

    # hammad.configuration
    from .configuration import (
        Configuration,
        read_configuration_from_os_vars,
        read_configuration_from_dotenv,
        read_configuration_from_file,
        read_configuration_from_url,
        read_configuration_from_os_prefix,
    )

    # hammad.data
    from .data import Collection, Database, create_collection, create_database

    # hammad.json
    from .json import encode_json, decode_json, convert_to_json_schema

    # hammad.logging
    from .logging import (
        Logger,
        create_logger,
        trace,
        trace_cls,
        trace_function,
        trace_http,
        install_trace_http,
    )

    # hammad.multithreading
    from .multithreading import (
        run_parallel,
        run_sequentially,
        run_with_retry,
        retry,
    )

    # hammad.pydantic
    from .pydantic import (
        convert_to_pydantic_field,
        convert_to_pydantic_model,
    )

    # hammad.text
    from .text import (
        Text,
        OutputText,
        SimpleText,
        convert_to_text,
        convert_type_to_text,
        convert_docstring_to_text,
    )

    # hammad.web
    from .web import (
        create_http_client,
        create_openapi_client,
        create_search_client,
        search_news,
        search_web,
        run_web_request,
        read_web_page,
        read_web_pages,
        extract_page_links,
    )

    # hammad.yaml
    from .yaml import encode_yaml, decode_yaml, read_yaml_file


__all__ = (
    # hammad.ai
    "create_completion",
    "async_create_completion",
    "create_embeddings",
    "async_create_embeddings",
    # hammad.base
    "Model",
    "field",
    "create_model",
    # hammad.cache
    "Cache",
    "cached",
    "auto_cached",
    "create_cache",
    # hammad.cli
    "print",
    "animate",
    "input",
    # hammad.configuration
    "Configuration",
    "read_configuration_from_os_vars",
    "read_configuration_from_dotenv",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_prefix",
    # hammad.data
    "Collection",
    "Database",
    "create_collection",
    "create_database",
    # hammad.json
    "encode_json",
    "decode_json",
    "convert_to_json_schema",
    # hammad.logging
    "Logger",
    "create_logger",
    "trace",
    "trace_cls",
    "trace_function",
    "trace_http",
    "install_trace_http",
    # hammad.multithreading
    "run_parallel",
    "run_sequentially",
    "run_with_retry",
    "retry",
    # hammad.pydantic
    "convert_to_pydantic_field",
    "convert_to_pydantic_model",
    # hammad.text
    "Text",
    "OutputText",
    "SimpleText",
    "convert_to_text",
    "convert_type_to_text",
    "convert_docstring_to_text",
    # hammad.web
    "create_http_client",
    "create_openapi_client",
    "create_search_client",
    "search_news",
    "search_web",
    "run_web_request",
    "read_web_page",
    "read_web_pages",
    "extract_page_links",
    # hammad.yaml
    "encode_yaml",
    "decode_yaml",
    "read_yaml_file",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
