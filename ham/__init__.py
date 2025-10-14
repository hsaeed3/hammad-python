"""ham"""

from .utils.type_checking_getattr_fn import (
    type_checking_getattr_fn,
    type_checking_dir_fn
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclasses import dataclass
    from pathlib._abc import ParserBase

__all__ = (
    "dataclass",
    "ParserBase",
)

__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)