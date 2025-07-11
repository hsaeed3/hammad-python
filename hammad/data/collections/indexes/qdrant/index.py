"""hammad.data.collections.indexes.qdrant.index"""

from datetime import datetime, timezone, timedelta
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
    final,
    TYPE_CHECKING,
    Tuple,
    NamedTuple,
)

if TYPE_CHECKING:
    from .....genai.models.embeddings.types import EmbeddingModelName
# import uuid  # Unused import
from pathlib import Path
import json

from ....sql.types import (
    DatabaseItemType,
    DatabaseItemFilters,
    DatabaseItem,
)
from ....sql.database import Database
from . import utils
from .settings import (
    QdrantCollectionIndexSettings,
    QdrantCollectionIndexQuerySettings,
    DistanceMetric,
)


class VectorSearchResult(NamedTuple):
    """Result from vector search containing item and similarity score."""

    item: "DatabaseItem[DatabaseItemType]"
    score: float


__all__ = (
    "QdrantCollectionIndex",
    "VectorSearchResult",
)


@final
class QdrantCollectionIndex:
    """A vector collection index that uses Qdrant for vector storage
    and similarity search, with SQL Database as the primary storage backend.

    This collection index provides vector-based functionality for storing
    embeddings and performing semantic similarity searches while using
    the Database class for reliable data persistence.
    """

    def __init__(
        self,
        *,
        name: str = "default",
        vector_size: Optional[int] = None,
        schema: Optional[Type[DatabaseItemType]] = None,
        ttl: Optional[int] = None,
        path: Optional[Path | str] = None,
        distance_metric: DistanceMetric = "dot",
        settings: Optional[QdrantCollectionIndexSettings] = None,
        query_settings: Optional[QdrantCollectionIndexQuerySettings] = None,
        embedding_model: Optional["EmbeddingModelName"] = None,
        embedding_dimensions: Optional[int] = None,
        embedding_api_key: Optional[str] = None,
        embedding_base_url: Optional[str] = None,
        rerank_model: Optional[str] = None,
        rerank_api_key: Optional[str] = None,
        rerank_base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize a new QdrantCollectionIndex.

        Args:
            name: The name of the index.
            vector_size: Size/dimension of the vectors to store.
            schema: Optional schema type for validation.
            ttl: The time to live for items in this index.
            path: The path where the index will be stored.
            distance_metric: Distance metric for similarity search.
            settings: Settings for Qdrant configuration.
            query_settings: Settings for query behavior.
            embedding_model: The embedding model to use (e.g., 'openai/text-embedding-3-small').
            embedding_dimensions: Number of dimensions for embeddings.
            embedding_api_key: API key for the embedding service.
            embedding_base_url: Base URL for the embedding service.
            rerank_model: The rerank model to use (e.g., 'cohere/rerank-english-v3.0').
            rerank_api_key: API key for the rerank service.
            rerank_base_url: Base URL for the rerank service.
        """
        self.name = name
        self.vector_size = vector_size
        self._vector_size_determined = vector_size is not None
        self.schema = schema
        self.ttl = ttl
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.embedding_api_key = embedding_api_key
        self.embedding_base_url = embedding_base_url
        self._embedding_function = None

        # Rerank model configuration
        self.rerank_model = rerank_model
        self.rerank_api_key = rerank_api_key
        self.rerank_base_url = rerank_base_url

        if path is not None and not isinstance(path, Path):
            path = Path(path)

        self.path = path

        # Create settings with vector_size and distance_metric
        if not settings:
            qdrant_path = None
            if self.path is not None:
                qdrant_path = str(self.path / f"{name}_qdrant")

            settings = QdrantCollectionIndexSettings(
                vector_size=vector_size or 768,  # Default fallback
                distance_metric=distance_metric,
                path=qdrant_path,
            )

        if not query_settings:
            query_settings = QdrantCollectionIndexQuerySettings()

        self.settings = settings
        self.query_settings = query_settings

        # Initialize SQL Database as primary storage backend
        database_path = None
        if self.path is not None:
            database_path = self.path / f"{name}.db"

        self._database = Database[DatabaseItemType](
            name=name,
            schema=schema,
            ttl=ttl,
            path=database_path,
            table_name=f"qdrant_{name}",
        )

        # Initialize Qdrant client (lazily to handle import errors gracefully)
        self._client = None
        self._client_wrapper = None
        # Only initialize if vector_size is determined
        if self._vector_size_determined:
            self._init_qdrant_client()

    def _init_qdrant_client(self) -> None:
        """Initialize Qdrant client and collection."""
        try:
            self._client = utils.create_qdrant_client(self.settings)
            self._client_wrapper = utils.QdrantClientWrapper(
                client=self._client, collection_name=self.name
            )

            # Create collection if it doesn't exist
            utils.create_collection_if_not_exists(
                self._client, self.name, self.settings
            )

        except utils.QdrantCollectionIndexError:
            # Qdrant not available - only SQL storage will work
            self._client = None
            self._client_wrapper = None

    def _get_embedding_function(self) -> Optional[Callable[[Any], List[float]]]:
        """Get or create embedding function from model configuration."""
        if self._embedding_function is None and self.embedding_model:
            from .....genai.models.embeddings.model import EmbeddingModel

            model = EmbeddingModel(model=self.embedding_model)

            def embedding_function(item: Any) -> List[float]:
                response = model.run(
                    input=item,
                    dimensions=self.embedding_dimensions,
                    api_key=self.embedding_api_key,
                    api_base=self.embedding_base_url,
                    format=True,
                )
                if response.data and len(response.data) > 0:
                    return response.data[0].embedding
                else:
                    raise utils.QdrantCollectionIndexError(
                        "Failed to generate embedding: empty response"
                    )

            self._embedding_function = embedding_function

        return self._embedding_function

    def _rerank_results(
        self,
        query: str,
        results: List[Tuple[DatabaseItem[DatabaseItemType], float]],
        top_n: Optional[int] = None,
    ) -> List[Tuple[DatabaseItem[DatabaseItemType], float]]:
        """
        Rerank search results using the configured rerank model.

        Args:
            query: The original search query
            results: List of (DatabaseItem, similarity_score) tuples
            top_n: Number of top results to return after reranking

        Returns:
            Reranked list of (DatabaseItem, rerank_score) tuples
        """
        if not self.rerank_model or not results:
            return results

        try:
            from .....genai.models.reranking import run_reranking_model

            # Extract documents for reranking
            documents = []
            for db_item, _ in results:
                # Convert item to string for reranking
                if isinstance(db_item.item, dict):
                    doc_text = json.dumps(db_item.item)
                else:
                    doc_text = str(db_item.item)
                documents.append(doc_text)

            # Perform reranking
            rerank_response = run_reranking_model(
                model=self.rerank_model,
                query=query,
                documents=documents,
                top_n=top_n or len(results),
                api_key=self.rerank_api_key,
                api_base=self.rerank_base_url,
            )

            # Reorder results based on rerank scores
            reranked_results = []
            for rerank_result in rerank_response.results:
                original_index = rerank_result.index
                rerank_score = rerank_result.relevance_score
                db_item = results[original_index][0]
                # Update the score on the DatabaseItem itself
                db_item.score = rerank_score
                reranked_results.append((db_item, rerank_score))

            return reranked_results

        except Exception:
            # If reranking fails, return original results
            return results

    def _prepare_vector(self, item: Any) -> List[float]:
        """Prepare vector from item using embedding function or direct vector."""
        embedding_function = self._get_embedding_function()
        if embedding_function:
            vector = embedding_function(item)
            # Determine vector size from first embedding if not set
            if not self._vector_size_determined:
                self._determine_vector_size(len(vector))
            return vector
        elif isinstance(item, dict) and "vector" in item:
            vector = item["vector"]
            # Determine vector size from first vector if not set
            if not self._vector_size_determined:
                self._determine_vector_size(len(vector))
            return utils.prepare_vector(vector, self.vector_size)
        elif isinstance(item, (list, tuple)):
            # Determine vector size from first vector if not set
            if not self._vector_size_determined:
                self._determine_vector_size(len(item))
            return utils.prepare_vector(item, self.vector_size)
        else:
            raise utils.QdrantCollectionIndexError(
                "Item must contain 'vector' key, be a vector itself, "
                "or embedding_model must be provided"
            )

    def _determine_vector_size(self, size: int) -> None:
        """Determine and set vector size based on first embedding/vector."""
        if not self._vector_size_determined:
            self.vector_size = size
            self._vector_size_determined = True

            # Update settings with determined vector size
            if self.settings:
                self.settings.vector_size = size

            # Initialize Qdrant client now that we have vector size
            self._init_qdrant_client()

    def _add_to_qdrant(
        self,
        item_id: str,
        vector: List[float],
        item: DatabaseItemType,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> None:
        """Add item to Qdrant vector store."""
        if not self._client:
            # Qdrant not available, skip vector indexing
            return

        try:
            try:
                from qdrant_client.models import PointStruct
            except ImportError:
                raise ImportError(
                    "Using Qdrant requires the `qdrant-client` package. Please install with: pip install 'hammad-python[genai]'"
                )

            # Prepare payload with metadata
            payload = {
                "item_data": json.dumps(utils.serialize(item)),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add filters as top-level payload fields
            if filters:
                for key, value in filters.items():
                    payload[key] = value

            # Create point and upsert to Qdrant
            point = PointStruct(id=item_id, vector=vector, payload=payload)

            self._client.upsert(collection_name=self.name, points=[point])

        except Exception:
            # Vector indexing failed, but data is still in SQL database
            pass

    def add(
        self,
        item: DatabaseItemType,
        *,
        id: Optional[str] = None,
        filters: Optional[DatabaseItemFilters] = None,
        ttl: Optional[int] = None,
        vector: Optional[List[float]] = None,
    ) -> str:
        """
        Add an item to the index.

        Args:
            item: The item to store.
            id: Optional ID (will generate UUID if not provided).
            filters: Optional filters/metadata.
            ttl: Optional TTL in seconds.
            vector: Optional pre-computed vector (if not provided, will use embedding_function).

        Returns:
            The ID of the stored item.
        """
        # Add to SQL database first
        item_id = self._database.add(
            item=item,
            id=id,
            filters=filters,
            ttl=ttl,
        )

        # Prepare vector for Qdrant storage
        if vector is None:
            try:
                prepared_vector = self._prepare_vector(item)
            except utils.QdrantCollectionIndexError:
                # Vector preparation failed, but item is still in database
                return item_id
        else:
            prepared_vector = utils.prepare_vector(vector, self.vector_size)

        # Add to Qdrant vector store
        self._add_to_qdrant(item_id, prepared_vector, item, filters)

        return item_id

    def get(
        self,
        id: str,
        *,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> Optional[DatabaseItem[DatabaseItemType]]:
        """
        Get an item by ID.

        Args:
            id: The item ID.
            filters: Optional filters to match.

        Returns:
            The database item or None if not found.
        """
        return self._database.get(id, filters=filters)

    def _vector_search(
        self,
        query_vector: Union[List[float], Any],
        *,
        filters: Optional[DatabaseItemFilters] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        query_text: Optional[str] = None,
        enable_rerank: bool = True,
        return_scores: bool = False,
    ) -> Union[List[DatabaseItem[DatabaseItemType]], List[VectorSearchResult]]:
        """
        Internal method to perform vector similarity search.

        Args:
            query_vector: Query vector for similarity search.
            filters: Optional filters to apply.
            limit: Maximum number of results.
            score_threshold: Minimum similarity score threshold.
            query_text: Optional original query text for reranking.
            enable_rerank: Whether to enable reranking if rerank model is configured.
            return_scores: Whether to return scores with results.

        Returns:
            List of matching database items sorted by similarity score (and reranked if enabled),
            or list of VectorSearchResult objects if return_scores is True.
        """
        if not self._client:
            # Qdrant not available, return empty results
            return []

        # Prepare query vector
        prepared_vector = utils.prepare_vector(query_vector, self.vector_size)

        try:
            # Build Qdrant filter
            qdrant_filter = utils.build_qdrant_filter(filters)

            # Perform search
            results = self._client.query_points(
                collection_name=self.name,
                query=prepared_vector,
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False,
            )

            # Get item IDs from results and fetch from database with scores
            db_items_with_scores = []
            for result in results.points:
                item_id = str(result.id)
                db_item = self._database.get(item_id, filters=filters)
                if db_item:
                    # Set the score on the DatabaseItem itself
                    db_item.score = result.score
                    db_items_with_scores.append((db_item, result.score))

            # Apply reranking if enabled and configured
            if enable_rerank and self.rerank_model and query_text:
                db_items_with_scores = self._rerank_results(
                    query=query_text, results=db_items_with_scores, top_n=limit
                )

            # Return results with or without scores based on return_scores parameter
            if return_scores:
                return [
                    VectorSearchResult(item=item, score=score)
                    for item, score in db_items_with_scores
                ]
            else:
                # Extract just the database items (without scores) for backward compatibility
                db_items = [item for item, score in db_items_with_scores]
                return db_items

        except Exception:
            # Vector search failed, return empty results
            return []

    def query(
        self,
        query: Optional[str] = None,
        *,
        filters: Optional[DatabaseItemFilters] = None,
        limit: Optional[int] = None,
        vector: bool = False,
        rerank: bool = False,
        query_vector: Optional[List[float]] = None,
        return_scores: bool = False,
    ) -> Union[List[DatabaseItem[DatabaseItemType]], List[VectorSearchResult]]:
        """
        Query items from the collection.

        Args:
            query: Search query string.
            filters: Optional filters to apply.
            limit: Maximum number of results.
            vector: Whether to use vector search (requires embedding_model to be configured).
            rerank: Whether to use reranking (requires rerank_model to be configured).
            query_vector: Optional pre-computed query vector for similarity search.
            return_scores: Whether to return similarity scores with results (only applies to vector search).

        Returns:
            List of matching database items, or list of VectorSearchResult objects if return_scores is True.
        """
        effective_limit = limit or self.query_settings.limit

        # If explicit vector is provided, use it directly
        if query_vector is not None:
            return self._vector_search(
                query_vector=query_vector,
                filters=filters,
                limit=effective_limit,
                score_threshold=self.query_settings.score_threshold,
                query_text=query,
                enable_rerank=rerank,
                return_scores=return_scores,
            )

        # If vector=True, use vector search with embedding model
        if vector:
            if not query:
                raise ValueError("Query string is required when vector=True")

            embedding_function = self._get_embedding_function()
            if not embedding_function:
                raise ValueError("Embedding model not configured for vector search")

            try:
                query_vector = embedding_function(query)
                return self._vector_search(
                    query_vector=query_vector,
                    filters=filters,
                    limit=effective_limit,
                    score_threshold=self.query_settings.score_threshold,
                    query_text=query,
                    enable_rerank=rerank,
                    return_scores=return_scores,
                )
            except Exception as e:
                raise ValueError(f"Failed to generate embedding for query: {e}")

        # If rerank=True but vector=False, perform both standard and vector search, then rerank
        if rerank and query:
            if not self.rerank_model:
                raise ValueError("Rerank model not configured")

            # Get results from both database and vector search (if possible)
            db_results = self._database.query(
                limit=effective_limit,
                order_by="created_at",
                ascending=False,
            )

            vector_results = []
            embedding_function = self._get_embedding_function()
            if embedding_function:
                try:
                    query_vector = embedding_function(query)
                    vector_results = self._vector_search(
                        query_vector=query_vector,
                        filters=filters,
                        limit=effective_limit,
                        score_threshold=self.query_settings.score_threshold,
                        query_text=query,
                        enable_rerank=False,  # We'll rerank combined results
                        return_scores=False,  # We handle scores separately in rerank mode
                    )
                except Exception:
                    pass

            # Combine and deduplicate results
            combined_results = []
            seen_ids = set()

            for result in db_results + vector_results:
                if result.id not in seen_ids:
                    combined_results.append((result, 0.0))  # Score placeholder
                    seen_ids.add(result.id)

            # Apply reranking to combined results
            if combined_results:
                reranked_results = self._rerank_results(
                    query=query, results=combined_results, top_n=effective_limit
                )
                # Scores are already set on the DatabaseItem objects by _rerank_results
                return [item for item, _ in reranked_results]

            return [item for item, _ in combined_results]

        # Default: fall back to database query
        return self._database.query(
            limit=effective_limit,
            order_by="created_at",
            ascending=False,
        )

    def delete(self, id: str) -> bool:
        """
        Delete an item by ID.

        Args:
            id: The item ID.

        Returns:
            True if item was deleted, False if not found.
        """
        # Delete from database
        deleted = self._database.delete(id)

        if deleted and self._client:
            # Delete from Qdrant
            try:
                self._client.delete(collection_name=self.name, points_selector=[id])
            except Exception:
                # Vector deletion failed, but item was removed from database
                pass

        return deleted

    def count(
        self,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> int:
        """
        Count items matching the filters.

        Args:
            filters: Optional filters to apply.

        Returns:
            Number of matching items.
        """
        if not self._client:
            # Use database count
            from ....sql.types import QueryFilter, QueryCondition

            query_filter = None
            if filters:
                conditions = [
                    QueryCondition(
                        field="filters", operator="contains", value=json.dumps(filters)
                    )
                ]
                query_filter = QueryFilter(conditions=conditions)

            return self._database.count(query_filter)

        try:
            # Use Qdrant count
            qdrant_filter = utils.build_qdrant_filter(filters)
            info = self._client.count(
                collection_name=self.name,
                count_filter=qdrant_filter,
                exact=self.query_settings.exact,
            )
            return info.count
        except Exception:
            # Fall back to database count
            return self._database.count()

    def clear(self) -> int:
        """
        Clear all items from the index.

        Returns:
            Number of items deleted.
        """
        count = self._database.clear()

        if self._client:
            # Clear Qdrant collection by recreating it
            try:
                utils.create_collection_if_not_exists(
                    self._client, self.name, self.settings
                )
            except Exception:
                pass

        return count

    def get_vector(self, id: str) -> Optional[List[float]]:
        """
        Get the vector for a specific item by ID.

        Args:
            id: The item ID.

        Returns:
            The vector or None if not found.
        """
        if not self._client:
            return None

        try:
            points = self._client.retrieve(
                collection_name=self.name,
                ids=[id],
                with_payload=False,
                with_vectors=True,
            )

            if not points:
                return None

            vector = points[0].vector
            if isinstance(vector, dict):
                # Handle named vectors if used
                return list(vector.values())[0] if vector else None
            return vector

        except Exception:
            return None

    def __repr__(self) -> str:
        """String representation of the index."""
        location = str(self.path) if self.path else "memory"
        vector_available = "yes" if self._client else "no"
        return f"<QdrantCollectionIndex name='{self.name}' location='{location}' vector_size={self.vector_size} qdrant_available={vector_available}>"
