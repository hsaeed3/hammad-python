"""hammad.data.collections.collection"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
    TYPE_CHECKING,
)
from pathlib import Path

if TYPE_CHECKING:
    from .indexes.tantivy.index import TantivyCollectionIndex
    from .indexes.qdrant.index import QdrantCollectionIndex, VectorSearchResult
    from .indexes.tantivy.settings import (
        TantivyCollectionIndexSettings,
        TantivyCollectionIndexQuerySettings,
    )
    from .indexes.qdrant.settings import (
        QdrantCollectionIndexSettings,
        QdrantCollectionIndexQuerySettings,
        DistanceMetric,
    )
    from ..sql.types import DatabaseItemType
    from ...genai.models.embeddings.types import EmbeddingModelName
else:
    from .indexes.tantivy.index import TantivyCollectionIndex
    from .indexes.qdrant.index import QdrantCollectionIndex, VectorSearchResult


__all__ = (
    "Collection",
    "VectorSearchResult",
)


class Collection:
    """
    A unified collection factory that creates the appropriate collection index type
    based on the provided parameters.

    This class acts as a factory and doesn't contain its own logic - it simply
    returns instances of TantivyCollectionIndex or QdrantCollectionIndex based on the
    vector parameter.

    The main difference from the old approach is that now collections are 'unified'
    - there's no separate collections interface. Each collection directly uses either
    a Tantivy or Qdrant index with SQL Database as the storage backend.
    """

    @overload
    def __new__(
        cls,
        name: str = "default",
        *,
        schema: Optional[Type["DatabaseItemType"]] = None,
        ttl: Optional[int] = None,
        path: Optional[Union[Path, str]] = None,
        vector: Literal[False] = False,
        # Tantivy-specific parameters
        fast: bool = True,
        settings: Optional["TantivyCollectionIndexSettings"] = None,
        query_settings: Optional["TantivyCollectionIndexQuerySettings"] = None,
    ) -> "TantivyCollectionIndex": ...

    @overload
    def __new__(
        cls,
        name: str = "default",
        *,
        schema: Optional[Type["DatabaseItemType"]] = None,
        ttl: Optional[int] = None,
        path: Optional[Union[Path, str]] = None,
        vector: Literal[True] = True,
        vector_size: Optional[int] = None,
        # Vector/Qdrant-specific parameters
        distance_metric: "DistanceMetric" = "dot",
        settings: Optional["QdrantCollectionIndexSettings"] = None,
        query_settings: Optional["QdrantCollectionIndexQuerySettings"] = None,
        embedding_model: Optional[
            "EmbeddingModelName"
        ] = "openai/text-embedding-3-small",
        embedding_dimensions: Optional[int] = None,
        embedding_api_key: Optional[str] = None,
        embedding_base_url: Optional[str] = None,
        # Rerank-specific parameters
        rerank_model: Optional[str] = None,
        rerank_api_key: Optional[str] = None,
        rerank_base_url: Optional[str] = None,
    ) -> "QdrantCollectionIndex": ...

    def __new__(
        cls,
        name: str = "default",
        *,
        schema: Optional[Type["DatabaseItemType"]] = None,
        ttl: Optional[int] = None,
        path: Optional[Union[Path, str]] = None,
        vector: bool = False,
        vector_size: Optional[int] = None,
        # Tantivy-specific parameters
        fast: bool = True,
        # Unified settings parameters
        settings: Optional[
            Union["TantivyCollectionIndexSettings", "QdrantCollectionIndexSettings"]
        ] = None,
        query_settings: Optional[
            Union[
                "TantivyCollectionIndexQuerySettings",
                "QdrantCollectionIndexQuerySettings",
            ]
        ] = None,
        # Vector/Qdrant-specific parameters
        distance_metric: "DistanceMetric" = "dot",
        embedding_model: Optional[
            "EmbeddingModelName"
        ] = "openai/text-embedding-3-small",
        embedding_dimensions: Optional[int] = None,
        embedding_api_key: Optional[str] = None,
        embedding_base_url: Optional[str] = None,
        # Rerank-specific parameters
        rerank_model: Optional[str] = None,
        rerank_api_key: Optional[str] = None,
        rerank_base_url: Optional[str] = None,
    ) -> Union["TantivyCollectionIndex", "QdrantCollectionIndex"]:
        """
        Create a collection of the specified type.

        Args:
            name: Name of the collection
            schema: Optional schema type for validation
            ttl: Default TTL for items in seconds
            path: File path for storage (None = in-memory)
            vector: Whether this is a vector collection (True) or text search collection (False)
            vector_size: Size of vectors (required for vector collections)

            # Tantivy parameters (for non-vector collections):
            fast: Whether to use fast schema building & indexing

            # Unified parameters:
            settings: Collection settings (TantivyCollectionIndexSettings or QdrantCollectionIndexSettings)
            query_settings: Query behavior settings (TantivyCollectionIndexQuerySettings or QdrantCollectionIndexQuerySettings)

            # Qdrant parameters (for vector collections):
            distance_metric: Distance metric for similarity search
            embedding_model: The embedding model to use (e.g., 'openai/text-embedding-3-small')
            embedding_dimensions: Number of dimensions for embeddings
            embedding_api_key: API key for the embedding service
            embedding_base_url: Base URL for the embedding service

            # Rerank parameters (for vector collections):
            rerank_model: The rerank model to use (e.g., 'cohere/rerank-english-v3.0')
            rerank_api_key: API key for the rerank service
            rerank_base_url: Base URL for the rerank service

        Returns:
            A TantivyCollectionIndex or QdrantCollectionIndex instance
        """
        if vector:
            # Vector collection using Qdrant
            return QdrantCollectionIndex(
                name=name,
                vector_size=vector_size,
                schema=schema,
                ttl=ttl,
                path=path,
                distance_metric=distance_metric,
                settings=settings,
                query_settings=query_settings,
                embedding_model=embedding_model,
                embedding_dimensions=embedding_dimensions,
                embedding_api_key=embedding_api_key,
                embedding_base_url=embedding_base_url,
                rerank_model=rerank_model,
                rerank_api_key=rerank_api_key,
                rerank_base_url=rerank_base_url,
            )
        else:
            # Text search collection using Tantivy
            return TantivyCollectionIndex(
                name=name,
                schema=schema,
                ttl=ttl,
                path=path,
                fast=fast,
                settings=settings,
                query_settings=query_settings,
            )


@overload
def create_collection(
    name: str = "default",
    *,
    schema: Optional[Type["DatabaseItemType"]] = None,
    ttl: Optional[int] = None,
    path: Optional[Union[Path, str]] = None,
    vector: Literal[False] = False,
    # Tantivy-specific parameters
    fast: bool = True,
    settings: Optional["TantivyCollectionIndexSettings"] = None,
    query_settings: Optional["TantivyCollectionIndexQuerySettings"] = None,
) -> "TantivyCollectionIndex": ...


@overload
def create_collection(
    name: str = "default",
    *,
    schema: Optional[Type["DatabaseItemType"]] = None,
    ttl: Optional[int] = None,
    path: Optional[Union[Path, str]] = None,
    vector: Literal[True],
    vector_size: Optional[int] = None,
    # Vector/Qdrant-specific parameters
    distance_metric: "DistanceMetric" = "dot",
    settings: Optional["QdrantCollectionIndexSettings"] = None,
    query_settings: Optional["QdrantCollectionIndexQuerySettings"] = None,
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
) -> "QdrantCollectionIndex": ...


def create_collection(
    name: str = "default",
    *,
    schema: Optional[Type["DatabaseItemType"]] = None,
    ttl: Optional[int] = None,
    path: Optional[Union[Path, str]] = None,
    vector: bool = False,
    vector_size: Optional[int] = None,
    # Tantivy-specific parameters
    fast: bool = True,
    # Unified settings parameters
    settings: Optional[
        Union["TantivyCollectionIndexSettings", "QdrantCollectionIndexSettings"]
    ] = None,
    query_settings: Optional[
        Union[
            "TantivyCollectionIndexQuerySettings", "QdrantCollectionIndexQuerySettings"
        ]
    ] = None,
    # Vector/Qdrant-specific parameters
    distance_metric: "DistanceMetric" = "dot",
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
) -> Union["TantivyCollectionIndex", "QdrantCollectionIndex"]:
    """
    Create a data collection of the specified type. Collections are a unified
    interface for creating searchable, vectorizable data stores.

    Args:
        name: Name of the collection
        schema: Optional schema type for validation
        ttl: Default TTL for items in seconds
        path: File path for storage (None = in-memory)
        vector: Whether this is a vector collection (True) or text search collection (False)
        vector_size: Size of vectors (required for vector collections)

        # Tantivy parameters (for non-vector collections):
        fast: Whether to use fast schema building & indexing

        # Unified parameters:
        settings: Collection settings (TantivyCollectionIndexSettings or QdrantCollectionIndexSettings)
        query_settings: Query behavior settings (TantivyCollectionIndexQuerySettings or QdrantCollectionIndexQuerySettings)

        # Qdrant parameters (for vector collections):
        distance_metric: Distance metric for similarity search
        embedding_model: The embedding model to use (e.g., 'openai/text-embedding-3-small')
        embedding_dimensions: Number of dimensions for embeddings
        embedding_api_key: API key for the embedding service
        embedding_base_url: Base URL for the embedding service

    Returns:
        A TantivyCollectionIndex or QdrantCollectionIndex instance
    """
    return Collection(
        name=name,
        schema=schema,
        ttl=ttl,
        path=path,
        vector=vector,
        vector_size=vector_size,
        fast=fast,
        settings=settings,
        query_settings=query_settings,
        distance_metric=distance_metric,
        embedding_function=embedding_function,
    )
