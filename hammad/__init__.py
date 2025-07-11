"""hammad-python"""

from __future__ import annotations

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer as __hammad_importer__

if TYPE_CHECKING:
    from ._main._fn import fn
    from ._main._new import new
    from ._main._run import run
    from ._main._to import to
    from .cli import print, input, animate


__all__ = (
    # top level namespace modules for
    # super duper fast access to things and stuff
    "run",
    "new",
    "to",
    "fn",
    # cli
    "print",
    "input",
    "animate",
)


__getattr__ = __hammad_importer__(__all__)


def __dir__() -> list[str]:
    return list(__all__)
