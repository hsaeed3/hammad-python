"""hammad.types

Contains functional aliases, types and model-like objects that are used
internally within the `hammad` package, as well as usable for
various other cases."""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .file import File, FileSource
