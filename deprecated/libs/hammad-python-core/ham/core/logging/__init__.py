"""ham.core.logging"""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer

if TYPE_CHECKING:
    from .logger import (
        Logger,
        get_logger,
        create_logger,
        create_logger_level,
        LoggerLevelName,
        LoggerLevelSettings,
    )
    from .decorators import (
        trace_function,
        trace_cls,
        trace,
        trace_http,
        install_trace_http,
    )


__all__ = (
    # ham.core.logging.logger
    "Logger",
    "get_logger",
    "create_logger",
    "create_logger_level",
    "LoggerLevelName",
    "LoggerLevelSettings",
    # ham.core.logging.decorators
    "trace_function",
    "trace_cls",
    "trace",
    "trace_http",
    "install_trace_http",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the logging module."""
    return list(__all__)
