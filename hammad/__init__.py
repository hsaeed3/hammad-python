"""hammad-python"""

from __future__ import annotations

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer as __hammad_importer__

if TYPE_CHECKING:
    # hammad.cache
    from .cache import cached, Cache

    # hammad.cli
    from .cli import print, animate, input

    # hammad.formatting
    from .formatting.json import convert_to_json_schema
    from .formatting.text import convert_to_text, convert_type_to_text

    # hammad.logging
    from .logging.logger import Logger, create_logger
    from .logging.decorators import trace, trace_cls, trace_function, trace_http


__all__ = [
    # hammad.cache
    "cached",
    "Cache",
    # hammad.cli
    "print",
    "animate",
    "input",
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
]


__getattr__ = __hammad_importer__(__all__)


def __dir__() -> list[str]:
    return __all__
