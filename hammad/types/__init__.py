"""hammad.types

Contains functional alias, or model-like objects that are meant to be used
by users as bases as well as for type hints. These objects define simple
interfaces for various types of common objects."""

from typing import TYPE_CHECKING
from ..performance.imports import create_getattr_importer


if TYPE_CHECKING:
    from .text import (
        BaseText,
        Text,
    )
    