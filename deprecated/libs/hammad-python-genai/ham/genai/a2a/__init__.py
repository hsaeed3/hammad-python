"""ham.genai.a2a"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from fasta2a import FastA2A
    from .workers import (
        as_a2a_app,
        GraphWorker,
        AgentWorker,
    )


__all__ = (
    # fasta2a
    "FastA2A",
    # ham.genai.a2a.workers
    "as_a2a_app",
    "GraphWorker",
    "AgentWorker",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
