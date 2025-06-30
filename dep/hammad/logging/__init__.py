"""hammad.logging"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

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


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the logging module."""
    return list(__all__)
