"""hammad.ai.embeddings.client.fastembed_text_embeddings_client"""

from typing import Any, List, Optional, Union, Literal
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
from ..._utils import (
    get_fastembed_text_embedding_model,
)


__all__ = (
    "FastEmbedTextEmbeddingsClient",
    "FastEmbedTextEmbeddingModel",
    "FastEmbedTextEmbeddingModelSettings",
)


FastEmbedTextEmbeddingModel = Literal[
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-small-zh-v1.5",
    "snowflake/snowflake-arctic-embed-xs",
    "sentence-transformers/all-MiniLM-L6-v2",
    "jinaai/jina-embeddings-v2-small-en",
    "BAAI/bge-small-en",
    "snowflake/snowflake-arctic-embed-s",
    "nomic-ai/nomic-embed-text-v1.5-Q",
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "Qdrant/clip-ViT-B-32-text",
    "jinaai/jina-embeddings-v2-base-de",
    "BAAI/bge-base-en",
    "snowflake/snowflake-arctic-embed-m",
    "nomic-ai/nomic-embed-text-v1.5",
    "jinaai/jina-embeddings-v2-base-en",
    "nomic-ai/nomic-embed-text-v1",
    "snowflake/snowflake-arctic-embed-m-long",
    "mixedbread-ai/mxbai-embed-large-v1",
    "jinaai/jina-embeddings-v2-base-code",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "snowflake/snowflake-arctic-embed-l",
    "thenlper/gte-large",
    "BAAI/bge-large-en-v1.5",
    "intfloat/multilingual-e5-large",
]
"""All supported text embedding models supported by `fastembed`."""


class FastEmbedTextEmbeddingModelSettings(TypedDict):
    """Valid settings for the `fastembed` text embedding models."""

    model: FastEmbedTextEmbeddingModel | str
    parallel: Optional[int]
    batch_size: Optional[int]
    format: bool


class FastEmbedTextEmbeddingError(Exception):
    """Exception raised when an error occurs while generating embeddings
    using `fastembed` text embedding models."""

    def __init__(self, message: str, response: Any):
        self.message = message
        self.response = response


def _parse_fastembed_response_to_embedding_response(
    response: Any,
    model: FastEmbedTextEmbeddingModel | str,
) -> EmbeddingResponse:
    """Parse the response from the `fastembed` text embedding model to an `EmbeddingResponse` object."""
    try:
        embedding_data: List[Embedding] = []

        # Convert generator to list if needed
        if hasattr(response, "__iter__") and not isinstance(response, (list, tuple)):
            response = list(response)

        for i, item in enumerate(response):
            # Ensure item is a list of floats
            if hasattr(item, "tolist"):
                item = item.tolist()
            elif not isinstance(item, list):
                item = list(item)

            embedding_data.append(
                Embedding(embedding=item, index=i, object="embedding")
            )

        return EmbeddingResponse(
            data=embedding_data,
            model=str(model),
            object="list",
            usage=EmbeddingUsage(prompt_tokens=0, total_tokens=0),
        )
    except Exception as e:
        raise FastEmbedTextEmbeddingError(
            f"Failed to parse fastembed response to embedding response: {e}",
            response,
        )


class FastEmbedTextEmbeddingsClient(BaseEmbeddingsClient):
    """Client for the `fastembed` text embedding models."""

    @staticmethod
    def embed(
        input: List[Any] | Any,
        model: FastEmbedTextEmbeddingModel | str,
        parallel: Optional[int] = None,
        batch_size: Optional[int] = None,
        format: bool = False,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for the given input using
        a valid `fastembed` text embedding model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            model (FastEmbedTextEmbeddingModel | str) : The model to use for generating embeddings.
            parallel (Optional[int]) : The number of parallel processes to use for the embedding.
            batch_size (Optional[int]) : The batch size to use for the embedding.
            format (bool) : Whether to format each non-string input as a markdown string.
            **kwargs : Any : Additional keyword arguments to pass to the `fastembed` text embedding model.

        Returns:
            EmbeddingResponse : The embedding response from the `fastembed` text embedding model.
        """
        if not isinstance(input, list):
            input = [input]

        if format:
            for i in input:
                try:
                    i = convert_to_text(i)
                except Exception as e:
                    raise FastEmbedTextEmbeddingError(
                        f"Failed to format input to text: {e}",
                        i,
                    )

        model = get_fastembed_text_embedding_model(model)

        try:
            response = model.embed(
                documents=input,
                parallel=parallel,
                batch_size=batch_size,
                **kwargs,
            )
        except Exception as e:
            raise FastEmbedTextEmbeddingError(
                f"Failed to generate embeddings: {e}",
                input,
            )

        return _parse_fastembed_response_to_embedding_response(response, str(model))

    @staticmethod
    async def async_embed(
        input: List[Any] | Any,
        model: FastEmbedTextEmbeddingModel | str,
        parallel: Optional[int] = None,
        batch_size: Optional[int] = None,
        format: bool = False,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Async generate embeddings for the given input using
        a valid `fastembed` text embedding model.

        Args:
            input (List[Any] | Any) : The input text / content to generate embeddings for.
            model (FastEmbedTextEmbeddingModel | str) : The model to use for generating embeddings.
            parallel (Optional[int]) : The number of parallel processes to use for the embedding.
            batch_size (Optional[int]) : The batch size to use for the embedding.
            format (bool) : Whether to format each non-string input as a markdown string.
            **kwargs : Any : Additional keyword arguments to pass to the `fastembed` text embedding model.

        Returns:
            EmbeddingResponse : The embedding response from the `fastembed` text embedding model.
        """
        return FastEmbedTextEmbeddingsClient.embed(
            input=input,
            model=model,
            parallel=parallel,
            batch_size=batch_size,
            format=format,
            **kwargs,
        )
