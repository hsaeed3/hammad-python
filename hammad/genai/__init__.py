"""hammad.genai"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .embedding_models import (
        EmbeddingModel,
        EmbeddingModelRequest,
        EmbeddingModelResponse,
        run_embedding_model,
        async_run_embedding_model
    )
    from .language_models import (
        LanguageModel,
        LanguageModelRequest,
        LanguageModelResponse,
        run_language_model,
        async_run_language_model,
    )


__all__ = (
    # hammad.genai.embedding_models
    "EmbeddingModel",
    "EmbeddingModelRequest",
    "EmbeddingModelResponse",
    "run_embedding_model",
    "async_run_embedding_model",

    # hammad.genai.language_models
    "LanguageModel",
    "LanguageModelRequest",
    "LanguageModelResponse",
    "run_language_model",
    "async_run_language_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the genai module."""
    return list(__all__)