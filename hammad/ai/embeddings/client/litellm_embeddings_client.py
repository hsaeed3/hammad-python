"""hammad.ai.embeddings.client.litellm_embeddings_client"""

from typing import Any, List, Literal, Optional
import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


from .base_embeddings_client import BaseEmbeddingsClient
from ..types import (
    Embedding,
    EmbeddingUsage,
    EmbeddingResponse,
)
from ....formatting.text.converters import convert_to_text
from ..._utils import get_litellm

__all__ = (
    "LiteLlmEmbeddingsClient",
    "LiteLlmEmbeddingModel",
    "LiteLlmEmbeddingModelSettings",
)


LiteLlmEmbeddingModel = Literal[
    # OpenAI Embedding Models
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
    # OpenAI Compatible Embedding Models
    "openai/text-embedding-3-small",
    "openai/text-embedding-3-large",
    "openai/text-embedding-ada-002",
    # Bedrock Embedding Models
    "amazon.titan-embed-text-v1",
    "cohere.embed-english-v3",
    "cohere.embed-multilingual-v3",
    # Cohere Embedding Models
    "embed-english-v3.0",
    "embed-english-light-v3.0",
    "embed-multilingual-v3.0",
    "embed-multilingual-light-v3.0",
    "embed-english-v2.0",
    "embed-english-light-v2.0",
    "embed-multilingual-v2.0",
    # NVIDIA NIM Embedding Models
    "nvidia_nim/NV-Embed-QA",
    "nvidia_nim/nvidia/nv-embed-v1",
    "nvidia_nim/nvidia/nv-embedqa-mistral-7b-v2",
    "nvidia_nim/nvidia/nv-embedqa-e5-v5",
    "nvidia_nim/nvidia/embed-qa-4",
    "nvidia_nim/nvidia/llama-3.2-nv-embedqa-1b-v1",
    "nvidia_nim/nvidia/llama-3.2-nv-embedqa-1b-v2",
    "nvidia_nim/snowflake/arctic-embed-l",
    "nvidia_nim/baai/bge-m3",
    # HuggingFace Embedding Models
    "huggingface/microsoft/codebert-base",
    "huggingface/BAAI/bge-large-zh",
    # Mistral AI Embedding Models
    "mistral/mistral-embed",
    # Gemini AI Embedding Models
    "gemini/text-embedding-004",
    # Vertex AI Embedding Models
    "vertex_ai/textembedding-gecko",
    "vertex_ai/textembedding-gecko-multilingual",
    "vertex_ai/textembedding-gecko-multilingual@001",
    "vertex_ai/textembedding-gecko@001",
    "vertex_ai/textembedding-gecko@003",
    "vertex_ai/text-embedding-preview-0409",
    "vertex_ai/text-multilingual-embedding-preview-0409",
    # Voyage AI Embedding Models
    "voyage/voyage-01",
    "voyage/voyage-lite-01",
    "voyage/voyage-lite-01-instruct",
    # Nebius AI Studio Embedding Models
    "nebius/BAAI/bge-en-icl",
    "nebius/BAAI/bge-multilingual-gemma2",
    "nebius/intfloat/e5-mistral-7b-instruct",
    # Ollama Embedding Models
    "ollama/granite-embedding:30m",
    "ollama/granite-embedding:278m",
    "ollama/snowflake-arctic-embed2",
    "ollama/bge-large",
    "ollama/paraphrase-multilingual",
    "ollama/bge-m3",
    "ollama/snowflake-arctic-embed",
    "ollama/mxbai-embed-large",
    "ollama/all-minilm",
    "ollama/nomic-embed-text",
]
"""Common embedding models supported by `litellm`."""


class LiteLlmEmbeddingModelSettings(TypedDict):
    """Valid settings for the `litellm` embedding models."""

    model: LiteLlmEmbeddingModel | str
    dimensions: Optional[int]
    encoding_format: Optional[str]
    timeout: Optional[int]
    api_base: Optional[str]
    api_version: Optional[str]
    api_key: Optional[str]
    api_type: Optional[str]
    caching: bool
    user: Optional[str]


class LiteLlmEmbeddingError(Exception):
    """Exception raised when an error occurs while generating embeddings
    using `litellm`."""

    def __init__(self, message: str, response: Any):
        self.message = message
        self.response = response
        super().__init__(self.message)


def _parse_litellm_response_to_embedding_response(response: Any) -> EmbeddingResponse:
    """Parse the response from `litellm` to an `EmbeddingResponse` object."""
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
        return EmbeddingResponse(
            data=embedding_data,
            model=response.model,
            object="list",
            usage=usage,
        )
    except Exception as e:
        raise LiteLlmEmbeddingError(
            f"Failed to parse litellm response to embedding response: {e}",
            response,
        )


class LiteLlmEmbeddingsClient(BaseEmbeddingsClient):
    """Embeddings provider client that utilizes the `litellm` module
    when generating embeddings."""

    @staticmethod
    async def async_embed(
        input: List[Any] | Any,
        model: LiteLlmEmbeddingModel | str,
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
    ) -> Embedding:
        """Asynchronously generate embeddings for the given input using
        a valid `litellm` model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            model (LiteLlmEmbeddingModel | str) : The model to use for generating embeddings.
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
            Embedding : The embedding generated for the given input.
        """
        if not isinstance(input, list):
            input = [input]

        if format:
            for i in input:
                try:
                    i = convert_to_text(i)
                except Exception as e:
                    raise LiteLlmEmbeddingError(
                        f"Failed to format input to text: {e}",
                        i,
                    )

        async_embedding_fn = get_litellm().aembedding

        try:
            response = await async_embedding_fn(
                model=model,
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
            raise e

        return _parse_litellm_response_to_embedding_response(response)

    @staticmethod
    def embed(
        input: List[Any] | Any,
        model: LiteLlmEmbeddingModel | str,
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
    ) -> Embedding:
        """Generate embeddings for the given input using
        a valid `litellm` model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            model (LiteLlmEmbeddingModel | str) : The model to use for generating embeddings.
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
            Embedding : The embedding generated for the given input.
        """
        if not isinstance(input, list):
            input = [input]

        if format:
            for i in input:
                try:
                    i = convert_to_text(i)
                except Exception as e:
                    raise LiteLlmEmbeddingError(
                        f"Failed to format input to text: {e}",
                        i,
                    )

        sync_embedding_fn = get_litellm().embedding

        try:
            response = sync_embedding_fn(
                model=model,
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
            raise e

        return _parse_litellm_response_to_embedding_response(response)
