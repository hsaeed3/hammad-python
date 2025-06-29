"""hammad.ai.embeddings.create"""

from typing import Any, List, Optional

from .types import (
    EmbeddingResponse,
)
from .client.fastembed_text_embeddings_client import (
    FastEmbedTextEmbeddingsClient,
    FastEmbedTextEmbeddingModel,
    FastEmbedTextEmbeddingModelSettings,
)
from .client.litellm_embeddings_client import (
    LiteLlmEmbeddingsClient,
    LiteLlmEmbeddingModel,
)


__all__ = ("async_create_embeddings", "create_embeddings")


async def async_create_embeddings(
    input: List[Any] | Any,
    model: FastEmbedTextEmbeddingModel | LiteLlmEmbeddingModel | str,
    format: bool = False,
    # LiteLLM Settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: Optional[int] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    api_type: Optional[str] = None,
    caching: bool = False,
    user: Optional[str] = None,
    # FastEmbed Settings
    parallel: Optional[int] = None,
    batch_size: Optional[int] = None,
    **kwargs: Any,
) -> EmbeddingResponse:
    """Asynchronously create embeddings for the given input using the specified model.

    Args:
        input (List[Any] | Any) : The input text / content to generate embeddings for.
        model (FastEmbedTextEmbeddingModel | LiteLlmEmbeddingModel | str) : The model to use for generating embeddings.
        format (bool) : Whether to format each non-string input as a markdown string.
        dimensions (Optional[int]) : The dimensions of the embedding. NOTE: LiteLLM models only
        encoding_format (Optional[str]) : The encoding format of the embedding. NOTE: LiteLLM models only
        timeout (Optional[int]) : The timeout for the embedding. NOTE: LiteLLM models only
        api_base (Optional[str]) : The base URL for the embedding API. NOTE: LiteLLM models only
        api_version (Optional[str]) : The version of the embedding API. NOTE: LiteLLM models only
        api_key (Optional[str]) : The API key for the embedding API. NOTE: LiteLLM models only
        api_type (Optional[str]) : The type of the embedding API. NOTE: LiteLLM models only
        caching (bool) : Whether to cache the embedding. NOTE: LiteLLM models only
        user (Optional[str]) : The user for the embedding. NOTE: LiteLLM models only
        parallel (Optional[int]) : The number of parallel processes to use for the embedding. NOTE: FastEmbed models only
        batch_size (Optional[int]) : The batch size to use for the embedding. NOTE: FastEmbed models only
        **kwargs : Any : Additional keyword arguments to pass to the embedding client.

    Returns:
        EmbeddingResponse : The embedding response from the embedding client.
    """

    if model.startswith("fastembed/"):
        model = model.split("fastembed/")[1]
        return await FastEmbedTextEmbeddingsClient.async_embed(
            input=input,
            model=model,
            parallel=parallel,
            batch_size=batch_size,
            format=format,
            **kwargs,
        )
    else:
        return await LiteLlmEmbeddingsClient.async_embed(
            input=input,
            model=model,
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
            **kwargs,
        )


def create_embeddings(
    input: List[Any] | Any,
    model: FastEmbedTextEmbeddingModel | LiteLlmEmbeddingModel | str,
    format: bool = False,
    # LiteLLM Settings
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: Optional[int] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    api_type: Optional[str] = None,
    caching: bool = False,
    user: Optional[str] = None,
    # FastEmbed Settings
    parallel: Optional[int] = None,
    batch_size: Optional[int] = None,
    **kwargs: Any,
) -> EmbeddingResponse:
    """Asynchronously create embeddings for the given input using the specified model.

    Args:
        input (List[Any] | Any) : The input text / content to generate embeddings for.
        model (FastEmbedTextEmbeddingModel | LiteLlmEmbeddingModel | str) : The model to use for generating embeddings.
        format (bool) : Whether to format each non-string input as a markdown string.
        dimensions (Optional[int]) : The dimensions of the embedding. NOTE: LiteLLM models only
        encoding_format (Optional[str]) : The encoding format of the embedding. NOTE: LiteLLM models only
        timeout (Optional[int]) : The timeout for the embedding. NOTE: LiteLLM models only
        api_base (Optional[str]) : The base URL for the embedding API. NOTE: LiteLLM models only
        api_version (Optional[str]) : The version of the embedding API. NOTE: LiteLLM models only
        api_key (Optional[str]) : The API key for the embedding API. NOTE: LiteLLM models only
        api_type (Optional[str]) : The type of the embedding API. NOTE: LiteLLM models only
        caching (bool) : Whether to cache the embedding. NOTE: LiteLLM models only
        user (Optional[str]) : The user for the embedding. NOTE: LiteLLM models only
        parallel (Optional[int]) : The number of parallel processes to use for the embedding. NOTE: FastEmbed models only
        batch_size (Optional[int]) : The batch size to use for the embedding. NOTE: FastEmbed models only
        **kwargs : Any : Additional keyword arguments to pass to the embedding client.

    Returns:
        EmbeddingResponse : The embedding response from the embedding client.
    """

    if model.startswith("fastembed/"):
        model = model.split("fastembed/")[1]
        return FastEmbedTextEmbeddingsClient.embed(
            input=input,
            model=model,
            parallel=parallel,
            batch_size=batch_size,
            format=format,
            **kwargs,
        )
    else:
        return LiteLlmEmbeddingsClient.embed(
            input=input,
            model=model,
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
            **kwargs,
        )
