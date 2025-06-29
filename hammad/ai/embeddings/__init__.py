"""hammad.ai.embeddings"""

from typing import TYPE_CHECKING
from ..._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .client.base_embeddings_client import BaseEmbeddingsClient
    from .client.fastembed_text_embeddings_client import FastEmbedTextEmbeddingsClient
    from .client.litellm_embeddings_client import LiteLlmEmbeddingsClient
    from .types import Embedding, EmbeddingResponse, EmbeddingUsage
    from .create import create_embeddings, async_create_embeddings


__all__ = (
    # hammad.ai.embeddings.client.base_embeddings_client
    "BaseEmbeddingsClient",
    # hammad.ai.embeddings.client.fastembed_text_embeddings_client
    "FastEmbedTextEmbeddingsClient",
    # hammad.ai.embeddings.client.litellm_embeddings_client
    "LiteLlmEmbeddingsClient",
    # hammad.ai.embeddings.types
    "Embedding",
    "EmbeddingResponse",
    "EmbeddingUsage",
    # hammad.ai.embeddings.create
    "create_embeddings",
    "async_create_embeddings",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
