"""hammad.genai.embedding_models.embedding_model"""

import asyncio
from dataclasses import dataclass
from typing import Any, List, Literal, Optional, TYPE_CHECKING
import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

if TYPE_CHECKING:
    from litellm import EmbeddingResponse as _LitellmEmbeddingResponse

from ..language_models.language_model import _AIProvider
from .embedding_model_request import EmbeddingModelRequest
from .embedding_model_name import EmbeddingModelName
from .embedding_model_response import (
    Embedding,
    EmbeddingUsage,
    EmbeddingModelResponse,
)
from ...formatting.text import convert_to_text


__all__ = (
    "EmbeddingModel",
    "EmbeddingModelError",
)


class EmbeddingModelError(Exception):
    """Exception raised when an error occurs while generating embeddings
    using an embedding model."""

    def __init__(self, message: str, response: Any):
        self.message = message
        self.response = response
        super().__init__(self.message)


def _parse_litellm_response_to_embedding_model_response(response: "_LitellmEmbeddingResponse") -> EmbeddingModelResponse:
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
            data=embedding_data,
            model=response.model,
            object="list",
            usage=usage,
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
    
    model: EmbeddingModelName = "openai/text-embedding-3-small"
    
    async def async_run(
        self,
        input: List[Any] | Any,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
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

        async_embedding_fn = _AIProvider.get_litellm().aembedding

        try:
            response = await async_embedding_fn(
                model=self.model,
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
            )
        except Exception as e:
            raise EmbeddingModelError(f"Error in embedding model request: {e}", response=None) from e

        return _parse_litellm_response_to_embedding_model_response(response)

    def run(
        self,
        input: List[Any] | Any,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
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
                api_base=api_base,
                api_version=api_version,
                api_key=api_key,
                api_type=api_type,
                caching=caching,
                user=user,
                format=format,
            )
        )