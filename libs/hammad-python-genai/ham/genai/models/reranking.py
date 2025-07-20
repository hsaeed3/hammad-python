"""hammad.genai.models.reranking"""

# yay litellm

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ..._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from litellm import (
        rerank as run_reranking_model,
        arerank as async_run_reranking_model,
    )


__all__ = (
    "run_reranking_model",
    "async_run_reranking_model",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
