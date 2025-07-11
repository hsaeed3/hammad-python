"""hammad.genai.embedding_models.embedding_model_run_params"""

import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict, Required, NotRequired
else:
    from typing_extensions import TypedDict, Required, NotRequired

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    Literal,
)

from .embedding_model_name import EmbeddingModelName

__all__ = [
    "EmbeddingModelRunParams",
]


class EmbeddingModelRunParams(TypedDict, total=False):
    """A request to an embedding model."""

    input: List[Any] | Any
    """The input items to embed."""

    model: EmbeddingModelName | str
    """The embedding model to use."""

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
