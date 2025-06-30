"""hammad.ai.embeddings.client.base_embeddings_client"""

from abc import ABC, abstractmethod

from ..types import (
    EmbeddingResponse,
)

__all__ = ("BaseEmbeddingsClient",)


class BaseEmbeddingsClient(ABC):
    """Base class for the various supported embeddings clients within
    the `hammad.ai` extension."""

    @staticmethod
    @abstractmethod
    def async_embed(input: list, model: str, **kwargs) -> EmbeddingResponse:
        """"""
        pass

    @staticmethod
    @abstractmethod
    def embed(input: list, model: str, **kwargs) -> EmbeddingResponse:
        """"""
        pass
