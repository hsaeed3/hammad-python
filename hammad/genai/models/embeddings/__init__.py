"""hammad.genai.models.embeddings"""

from typing import TYPE_CHECKING
from ...._internal import create_getattr_importer


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


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Return the list of attributes to be shown in the REPL."""
    return __all__
