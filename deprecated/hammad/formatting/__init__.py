"""hammad.formatting"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from . import json
    from .json import (
        convert_to_json_schema
    )
    from . import text
    from .text import (
        convert_to_text,
        convert_type_to_text,
        convert_docstring_to_text
    )
    from . import yaml

__all__ = (
    "json",
    "convert_to_json_schema",
    "text",
    "convert_to_text",
    "convert_type_to_text",
    "convert_docstring_to_text",
    "yaml",
)

__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
