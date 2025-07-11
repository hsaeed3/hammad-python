"""hammad.formatting"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from . import json
    from . import text
    from . import yaml

__all__ = (
    "json",
    "text",
    "yaml",
)

__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
