"""hammad.genai.models.embeddings.types"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ....core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from .embedding_model_name import EmbeddingModelName
    from .embedding_model_run_params import EmbeddingModelRunParams
    from .embedding_model_response import (
        Embedding,
        EmbeddingUsage,
        EmbeddingModelResponse,
    )
    from .embedding_model_settings import EmbeddingModelSettings


__all__ = [
    # ham.genai.models.embeddings.types.embedding_model_name
    "EmbeddingModelName",
    # ham.genai.models.embeddings.types.embedding_model_run_params
    "EmbeddingModelRunParams",
    # ham.genai.models.embeddings.types.embedding_model_response
    "Embedding",
    "EmbeddingUsage",
    "EmbeddingModelResponse",
    # ham.genai.models.embeddings.types.embedding_model_settings
    "EmbeddingModelSettings",
]


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Return the list of attributes to be shown in the REPL."""
    return __all__
