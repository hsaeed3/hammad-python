"""hammad.genai.embedding_models.run

Standalone functions for running embedding models with full parameter typing.
"""

from typing import Any, List, Optional, overload, Union

from .types import (
    EmbeddingModelName,
    EmbeddingModelResponse,
)
from .model import EmbeddingModel

__all__ = [
    "run_embedding_model",
    "async_run_embedding_model",
]


# Overloads for run_embedding_model
@overload
def run_embedding_model(
    input: List[Any] | Any,
    *,
    # Provider settings
    model: EmbeddingModelName = "openai/text-embedding-3-small",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    api_type: Optional[str] = None,
    # Extended settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: int = 600,
    caching: bool = False,
    user: Optional[str] = None,
    format: bool = False,
) -> EmbeddingModelResponse: ...


def run_embedding_model(
    input: List[Any] | Any,
    *,
    # Provider settings
    model: EmbeddingModelName = "openai/text-embedding-3-small",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    api_type: Optional[str] = None,
    # Extended settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: int = 600,
    caching: bool = False,
    user: Optional[str] = None,
    format: bool = False,
) -> EmbeddingModelResponse:
    """Run an embedding model with the given input.

    Args:
        input: The input text/content to generate embeddings for
        model: The embedding model to use
        api_base: The base URL for the API
        api_key: The API key to use for the request
        api_version: The version of the API
        api_type: The API type to use for the request
        dimensions: The number of dimensions for the embedding
        encoding_format: The format to return the embeddings in
        timeout: The timeout for the request
        caching: Whether to cache the request
        user: The user to use for the request
        format: Whether to format each non-string input as a markdown string

    Returns:
        EmbeddingModelResponse: The embedding response
    """
    embedding_model = EmbeddingModel(model=model)
    return embedding_model.run(
        input=input,
        dimensions=dimensions,
        encoding_format=encoding_format,
        timeout=timeout,
        api_base=api_base,
        api_version=api_version,
        api_key=api_key,
        api_type=api_type,
        caching=caching,
        user=user,
        format=format,
    )


# Overloads for async_run_embedding_model
@overload
async def async_run_embedding_model(
    input: List[Any] | Any,
    *,
    # Provider settings
    model: EmbeddingModelName = "openai/text-embedding-3-small",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    api_type: Optional[str] = None,
    # Extended settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: int = 600,
    caching: bool = False,
    user: Optional[str] = None,
    format: bool = False,
) -> EmbeddingModelResponse: ...


async def async_run_embedding_model(
    input: List[Any] | Any,
    *,
    # Provider settings
    model: EmbeddingModelName = "openai/text-embedding-3-small",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    api_type: Optional[str] = None,
    # Extended settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: int = 600,
    caching: bool = False,
    user: Optional[str] = None,
    format: bool = False,
) -> EmbeddingModelResponse:
    """Asynchronously run an embedding model with the given input.

    Args:
        input: The input text/content to generate embeddings for
        model: The embedding model to use
        api_base: The base URL for the API
        api_key: The API key to use for the request
        api_version: The version of the API
        api_type: The API type to use for the request
        dimensions: The number of dimensions for the embedding
        encoding_format: The format to return the embeddings in
        timeout: The timeout for the request
        caching: Whether to cache the request
        user: The user to use for the request
        format: Whether to format each non-string input as a markdown string

    Returns:
        EmbeddingModelResponse: The embedding response
    """
    embedding_model = EmbeddingModel(model=model)
    return await embedding_model.async_run(
        input=input,
        dimensions=dimensions,
        encoding_format=encoding_format,
        timeout=timeout,
        api_base=api_base,
        api_version=api_version,
        api_key=api_key,
        api_type=api_type,
        caching=caching,
        user=user,
        format=format,
    )
