"""hammad.genai.models.embeddings.types"""

from typing import TYPE_CHECKING
from ....._internal import create_getattr_importer


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
    # hammad.genai.models.embeddings.types.embedding_model_name
    "EmbeddingModelName",
    # hammad.genai.models.embeddings.types.embedding_model_run_params
    "EmbeddingModelRunParams",
    # hammad.genai.models.embeddings.types.embedding_model_response
    "Embedding",
    "EmbeddingUsage",
    "EmbeddingModelResponse",
    # hammad.genai.models.embeddings.types.embedding_model_settings
    "EmbeddingModelSettings",
]


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Return the list of attributes to be shown in the REPL."""
    return __all__
