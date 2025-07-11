"""hammad.genai.rerank_models"""

# yay litellm

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer


if TYPE_CHECKING:
    from litellm import (
        rerank as run_rerank_model,
        arerank as async_run_rerank_model,
    )


__all__ = (
    "run_rerank_model",
    "async_run_rerank_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)