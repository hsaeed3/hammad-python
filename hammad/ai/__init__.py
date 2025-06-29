"""hammad.ai"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .completions import (
        CompletionsClient,
        Completion,
        CompletionChunk,
        CompletionsInputParam,
        CompletionsModelName,
        CompletionsOutputType,
        CompletionStream,
        AsyncCompletionStream,
        async_create_completion,
        create_completion,
    )
    from .embeddings import (
        Embedding,
        EmbeddingResponse,
        EmbeddingUsage,
        BaseEmbeddingsClient,
        FastEmbedTextEmbeddingsClient,
        LiteLlmEmbeddingsClient,
        create_embeddings,
        async_create_embeddings,
    )


__all__ = (
    # hammad.ai.completions
    "CompletionsClient",
    "Completion",
    "CompletionChunk",
    "CompletionsInputParam",
    "CompletionsModelName",
    "CompletionsOutputType",
    "CompletionStream",
    "AsyncCompletionStream",
    "async_create_completion",
    "create_completion",
    # hammad.ai.embeddings
    "Embedding",
    "EmbeddingResponse",
    "EmbeddingUsage",
    "BaseEmbeddingsClient",
    "FastEmbedTextEmbeddingsClient",
    "LiteLlmEmbeddingsClient",
    "create_embeddings",
    "async_create_embeddings",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
