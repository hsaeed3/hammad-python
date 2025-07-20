"""ham.genai.types"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ..core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from .history import History
    from .tools import Tool


__all__ = ("Tool", "History")


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
