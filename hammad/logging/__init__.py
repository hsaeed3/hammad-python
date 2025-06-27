"""hammad.logging"""

from typing import TYPE_CHECKING
from ..based.utils import auto_create_lazy_loader

if TYPE_CHECKING:
    from .logger import Logger, create_logger, create_logger_level
    from .decorators import trace_function, trace_cls, trace


__all__ = (
    "Logger",
    "LoggerLevel",
    "create_logger",
    "create_logger_level",
    "trace_function",
    "trace_cls",
    "trace",
)


__getattr__ = auto_create_lazy_loader(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the logging module."""
    return list(__all__)
