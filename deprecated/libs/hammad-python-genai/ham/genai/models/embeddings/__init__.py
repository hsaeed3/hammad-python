"""hammad.genai.models.embeddings"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ..._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from .model import (
        EmbeddingModel,
        create_embedding_model,
    )
    from .run import (
        run_embedding_model,
        async_run_embedding_model,
    )
    from .types import (
        Embedding,
        EmbeddingModelResponse,
        EmbeddingModelSettings,
    )


__all__ = [
    "EmbeddingModel",
    "create_embedding_model",
    # hammad.genai.models.embeddings.run
    "run_embedding_model",
    "async_run_embedding_model",
    # hammad.genai.models.embeddings.types.embedding
    "Embedding",
    # hammad.genai.models.embeddings.types.embedding_model_response
    "EmbeddingModelResponse",
    # hammad.genai.models.embeddings.types.embedding_model_settings
    "EmbeddingModelSettings",
]


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    """Return the list of attributes to be shown in the REPL."""
    return __all__
