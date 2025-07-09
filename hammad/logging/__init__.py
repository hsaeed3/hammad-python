"""hammad.logging"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .logger import Logger, create_logger, create_logger_level, LoggerLevelName
    from .decorators import (
        trace_function,
        trace_cls,
        trace,
        trace_http,
        install_trace_http,
    )


__all__ = (
    "Logger",
    "LoggerLevelName",
    "create_logger",
    "create_logger_level",
    "trace_function",
    "trace_cls",
    "trace",
    "trace_http",
    "install_trace_http",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the logging module."""
    return list(__all__)
