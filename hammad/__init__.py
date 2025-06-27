"""hammad-python

A collection of rapid, opinionated, cookie-cutter like resources for
Python applications and development."""

# NOTE:
# all resources imported to the top level are lazy loaded within their
# respective modules.

# `hammad.based`
from .based import (
    BasedModel,
    basedfield,
    based_validator,
    create_basedmodel,
)
from .based.utils import install, is_basedfield, is_basedmodel

# `hammad.cache`
from .cache import cached, auto_cached, create_cache

# `hammad.cli`
from .cli import input, print, animate

# `hammad.data`
from .data import create_collection, create_database

# `hammad.json`
from .json import convert_to_json_schema

# `hammad.logging`
from .logging import (
    create_logger,
    create_logger_level,
    # NOTE: decorators
    trace,
    trace_cls,
    trace_function,
)

# `hammad.pydantic`
from .pydantic import (
    convert_to_pydantic_model,
    convert_to_pydantic_field,
    create_confirmation_pydantic_model,
    create_selection_pydantic_model,
)

# `hammad.text`
from .text import (
    convert_docstring_to_text,
    convert_to_text,
    convert_type_to_text,
)

# `hammad.web`
from .web import (
    create_http_client,
    create_openapi_client,
    create_search_client,
    read_web_page,
    read_web_pages,
    run_web_request,
    search_news,
    search_web,
    extract_page_links,
)
