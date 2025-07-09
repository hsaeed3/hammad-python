"""hammad.genai.embedding_models"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .embedding_model import EmbeddingModel
    from .embedding_model_request import EmbeddingModelRequest
    from .embedding_model_response import EmbeddingModelResponse
    from .embedding_model_name import EmbeddingModelName
    from .run import (
        run_embedding_model,
        async_run_embedding_model,
    )


__all__ = (
    # hammad.genai.embedding_models.embedding_model
    "EmbeddingModel",

    # hammad.genai.embedding_models.embedding_model_request
    "EmbeddingModelRequest",

    # hammad.genai.embedding_models.embedding_model_response
    "EmbeddingModelResponse",

    # hammad.genai.embedding_models.embedding_model_name
    "EmbeddingModelName",

    # hammad.genai.embedding_models.run
    "run_embedding_model",
    "async_run_embedding_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the embedding_models module."""
    return list(__all__)