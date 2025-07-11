"""hammad.genai.models.embeddings.types.embedding_model_settings"""

from pydantic import BaseModel
from typing import Any, List, Optional

from .embedding_model_name import EmbeddingModelName
from ....types.base import BaseGenAIModelSettings


__all__ = [
    "EmbeddingModelSettings",
]


class EmbeddingModelSettings(BaseGenAIModelSettings):
    """A request to an embedding model."""

    format: bool = False
    """Whether to format each non-string input as a markdown string."""

    # LiteLLM Settings
    dimensions: Optional[int] = None
    """The dimensions of the embedding."""

    encoding_format: Optional[str] = None
    """The encoding format of the embedding."""

    timeout: Optional[int] = None
    """The timeout for the embedding request."""

    api_base: Optional[str] = None
    """The API base for the embedding request."""

    api_version: Optional[str] = None
    """The API version for the embedding request."""

    api_key: Optional[str] = None
    """The API key for the embedding request."""

    api_type: Optional[str] = None
    """The API type for the embedding request."""

    caching: bool = False
    """Whether to cache the embedding request."""

    user: Optional[str] = None
    """The user for the embedding request."""
