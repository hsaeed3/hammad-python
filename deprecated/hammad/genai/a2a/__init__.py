"""hammad.genai.a2a"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from fasta2a import (
        FastA2A
    )
    from .workers import (
        as_a2a_app,
        GraphWorker,
        AgentWorker,
    )


__all__ = (
    # fasta2a
    "FastA2A",
    # hammad.genai.a2a.workers
    "as_a2a_app",
    "GraphWorker",
    "AgentWorker",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)