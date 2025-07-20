"""hammad.genai.embedding_models.embedding_model"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, List, Optional
import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from ..model_provider import litellm

from .types import (
    EmbeddingModelName,
    EmbeddingModelRunParams,
    EmbeddingModelSettings,
    Embedding,
    EmbeddingUsage,
    EmbeddingModelResponse,
)
from ....formatting.text import convert_to_text


__all__ = (
    "EmbeddingModel",
    "EmbeddingModelError",
    "create_embedding_model",
)


class EmbeddingModelError(Exception):
    """Exception raised when an error occurs while generating embeddings
    using an embedding model."""

    def __init__(self, message: str, response: Any):
        self.message = message
        self.response = response
        super().__init__(self.message)


def _parse_litellm_response_to_embedding_model_response(
    response: "litellm.EmbeddingResponse",
) -> EmbeddingModelResponse:
    """Parse the response from `litellm` to an `EmbeddingModelResponse` object."""
    try:
        embedding_data: List[Embedding] = []

        for i, item in enumerate(response.data):
            embedding_data.append(
                Embedding(embedding=item["embedding"], index=i, object="embedding")
            )
        usage = EmbeddingUsage(
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
        )
        return EmbeddingModelResponse(
            output=embedding_data,
            model=response.model,
            object="list",
            usage=usage,
            type="embedding_model",
        )
    except Exception as e:
        raise EmbeddingModelError(
            f"Failed to parse litellm response to embedding response: {e}",
            response,
        )


@dataclass
class EmbeddingModel:
    """Embeddings provider client that utilizes the `litellm` module
    when generating embeddings."""

    model: EmbeddingModelName | str = "openai/text-embedding-3-small"

    base_url: Optional[str] = None
    """Optional base URL for a custom embedding provider."""

    api_key: Optional[str] = None
    """Optional API key for a custom embedding provider."""

    api_type: Optional[str] = None
    """Optional API type for a custom embedding provider."""

    api_version: Optional[str] = None
    """Optional API version for a custom embedding provider."""

    settings: EmbeddingModelSettings = field(default_factory=EmbeddingModelSettings)
    """Optional settings for the embedding model."""

    async def async_run(
        self,
        input: List[Any] | Any,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600,
        caching: bool = False,
        user: Optional[str] = None,
        format: bool = False,
    ) -> EmbeddingModelResponse:
        """Asynchronously generate embeddings for the given input using
        a valid `litellm` model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            dimensions (Optional[int]) : The number of dimensions for the embedding.
            encoding_format (Optional[str]) : The format to return the embeddings in. (e.g. "float", "base64")
            timeout (int) : The timeout for the request.
            api_base (Optional[str]) : The base URL for the API.
            api_version (Optional[str]) : The version of the API.
            api_key (Optional[str]) : The API key to use for the request.
            api_type (Optional[str]) : The API type to use for the request.
            caching (bool) : Whether to cache the request.
            user (Optional[str]) : The user to use for the request.
            format (bool) : Whether to format each non-string input as a markdown string.

        Returns:
            EmbeddingModelResponse : The embedding response generated for the given input.
        """
        if not isinstance(input, list):
            input = [input]

        if format:
            for i in input:
                try:
                    i = convert_to_text(i)
                except Exception as e:
                    raise EmbeddingModelError(
                        f"Failed to format input to text: {e}",
                        i,
                    )

        async_embedding_fn = litellm.aembedding

        try:
            response = await async_embedding_fn(
                model=self.model,
                input=input,
                dimensions=dimensions or self.settings.dimensions,
                encoding_format=encoding_format or self.settings.encoding_format,
                timeout=timeout or self.settings.timeout,
                api_base=self.base_url or self.settings.api_base,
                api_version=self.api_version or self.settings.api_version,
                api_key=self.api_key or self.settings.api_key,
                api_type=self.api_type or self.settings.api_type,
                caching=caching or self.settings.caching,
                user=user or self.settings.user,
            )
        except Exception as e:
            raise EmbeddingModelError(
                f"Error in embedding model request: {e}", response=None
            ) from e

        return _parse_litellm_response_to_embedding_model_response(response)

    def run(
        self,
        input: List[Any] | Any,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600,
        caching: bool = False,
        user: Optional[str] = None,
        format: bool = False,
    ) -> EmbeddingModelResponse:
        """Generate embeddings for the given input using
        a valid `litellm` model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            dimensions (Optional[int]) : The number of dimensions for the embedding.
            encoding_format (Optional[str]) : The format to return the embeddings in. (e.g. "float", "base64")
            timeout (int) : The timeout for the request.
            api_base (Optional[str]) : The base URL for the API.
            api_version (Optional[str]) : The version of the API.
            api_key (Optional[str]) : The API key to use for the request.
            api_type (Optional[str]) : The API type to use for the request.
            caching (bool) : Whether to cache the request.
            user (Optional[str]) : The user to use for the request.
            format (bool) : Whether to format each non-string input as a markdown string.

        Returns:
            EmbeddingModelResponse : The embedding response generated for the given input.
        """
        return asyncio.run(
            self.async_run(
                input=input,
                dimensions=dimensions,
                encoding_format=encoding_format,
                timeout=timeout,
                caching=caching,
                user=user,
                format=format,
            )
        )


def create_embedding_model(
    model: str | EmbeddingModelName = "openai/text-embedding-3-small",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    api_type: Optional[str] = None,
    settings: Optional[EmbeddingModelSettings] = None,
) -> EmbeddingModel:
    """Create an embedding model instance.

    Args:
        model (str | EmbeddingModelName) : The model to use for the embedding.
        base_url (Optional[str]) : The base URL for the API.
        api_key (Optional[str]) : The API key to use for the request.
        api_version (Optional[str]) : The version of the API.
        api_type (Optional[str]) : The API type to use for the request.
        settings (Optional[EmbeddingModelSettings]) : The settings for the embedding model.
    """
    return EmbeddingModel(
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_version=api_version,
        api_type=api_type,
        settings=settings or EmbeddingModelSettings(),
    )
