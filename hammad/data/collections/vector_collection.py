"""hammad.data.collections.vector_collection"""

import uuid
from typing import Any, Dict, Optional, List, Generic, Union, Callable
from datetime import datetime, timezone, timedelta

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        SearchRequest,
        QueryResponse,
    )
    import numpy as np
except ImportError as e:
    raise ImportError(
        "qdrant-client is required for VectorCollection. "
        "Install with: pip install qdrant-client"
        "Or install the the `ai` extra: `pip install hammad-python[ai]`"
    ) from e

from .base_collection import BaseCollection, Object, Filters, Schema

__all__ = ("VectorCollection",)


class VectorCollection(BaseCollection, Generic[Object]):
    """
    Vector collection class that uses Qdrant for vector storage and similarity search.

    This provides vector-based functionality for storing embeddings and performing
    semantic similarity searches.
    """

    # Namespace UUID for generating deterministic UUIDs from string IDs
    _NAMESPACE_UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    def __init__(
        self,
        name: str,
        vector_size: int,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        storage_backend: Optional[Any] = None,
        distance_metric: Distance = Distance.DOT,
        qdrant_config: Optional[Dict[str, Any]] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
    ):
        """
        Initialize a vector collection.

        Args:
            name: The name of the collection
            vector_size: Size/dimension of the vectors to store
            schema: Optional schema for type validation
            default_ttl: Default TTL for items in seconds
            storage_backend: Optional storage backend (Database instance or custom)
            distance_metric: Distance metric for similarity search (COSINE, DOT, EUCLID, MANHATTAN)
            qdrant_config: Optional Qdrant configuration
                          Example: {
                              "path": "/path/to/db",  # For persistent storage
                              "host": "localhost",    # For remote Qdrant
                              "port": 6333,
                              "grpc_port": 6334,
                              "prefer_grpc": True,
                              "api_key": "your-api-key"
                          }
            embedding_function: Optional function to convert objects to vectors
        """
        self.name = name
        self.vector_size = vector_size
        self.schema = schema
        self.default_ttl = default_ttl
        self.distance_metric = distance_metric
        self._storage_backend = storage_backend
        self._embedding_function = embedding_function

        # Store qdrant configuration
        self._qdrant_config = qdrant_config or {}

        # In-memory storage when used independently
        self._items: Dict[str, Dict[str, Any]] = {}

        # Mapping from original IDs to UUIDs
        self._id_mapping: Dict[str, str] = {}

        # Initialize Qdrant client
        self._init_qdrant_client()

    def _init_qdrant_client(self):
        """Initialize the Qdrant client and collection."""
        config = self._qdrant_config

        if "path" in config:
            # Persistent local storage
            self._client = QdrantClient(path=config["path"])
        elif "host" in config:
            # Remote Qdrant server
            self._client = QdrantClient(
                host=config.get("host", "localhost"),
                port=config.get("port", 6333),
                grpc_port=config.get("grpc_port", 6334),
                prefer_grpc=config.get("prefer_grpc", False),
                api_key=config.get("api_key"),
                timeout=config.get("timeout"),
            )
        else:
            # In-memory database (default)
            self._client = QdrantClient(":memory:")

        # Create collection if it doesn't exist
        try:
            collections = self._client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.name not in collection_names:
                self._client.create_collection(
                    collection_name=self.name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=self.distance_metric
                    ),
                )
        except Exception as e:
            # Collection might already exist or other issue
            pass

    def _ensure_uuid(self, id_str: str) -> str:
        """Convert a string ID to a UUID string, or validate if already a UUID."""
        # Check if it's already a valid UUID
        try:
            uuid.UUID(id_str)
            return id_str
        except ValueError:
            # Not a valid UUID, create a deterministic one
            new_uuid = str(uuid.uuid5(self._NAMESPACE_UUID, id_str))
            self._id_mapping[id_str] = new_uuid
            return new_uuid

    def __repr__(self) -> str:
        item_count = len(self._items) if self._storage_backend is None else "managed"
        return f"<{self.__class__.__name__} name='{self.name}' vector_size={self.vector_size} items={item_count}>"

    def _calculate_expires_at(self, ttl: Optional[int]) -> Optional[datetime]:
        """Calculate expiry time based on TTL."""
        if ttl is None:
            ttl = self.default_ttl
        if ttl and ttl > 0:
            return datetime.now(timezone.utc) + timedelta(seconds=ttl)
        return None

    def _is_expired(self, expires_at: Optional[datetime]) -> bool:
        """Check if an item has expired."""
        if expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now >= expires_at

    def _match_filters(
        self, stored: Optional[Filters], query: Optional[Filters]
    ) -> bool:
        """Check if stored filters match query filters."""
        if query is None:
            return True
        if stored is None:
            return False
        return all(stored.get(k) == v for k, v in query.items())

    def _prepare_vector(self, entry: Any) -> List[float]:
        """Prepare vector from entry using embedding function or direct vector."""
        if self._embedding_function:
            return self._embedding_function(entry)
        elif isinstance(entry, dict) and "vector" in entry:
            vector = entry["vector"]
            if isinstance(vector, np.ndarray):
                return vector.tolist()
            elif isinstance(vector, list):
                return vector
            else:
                raise ValueError("Vector must be a list or numpy array")
        elif isinstance(entry, (list, np.ndarray)):
            if isinstance(entry, np.ndarray):
                return entry.tolist()
            return entry
        else:
            raise ValueError(
                "Entry must contain 'vector' key, be a vector itself, "
                "or embedding_function must be provided"
            )

    def _build_qdrant_filter(self, filters: Optional[Filters]) -> Optional[Filter]:
        """Build Qdrant filter from filters dict."""
        if not filters:
            return None

        conditions = []
        for key, value in filters.items():
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        if len(conditions) == 1:
            return Filter(must=[conditions[0]])
        else:
            return Filter(must=conditions)

    def get(self, id: str, *, filters: Optional[Filters] = None) -> Optional[Object]:
        """Get an item by ID."""
        if self._storage_backend is not None:
            # Delegate to storage backend (Database instance)
            return self._storage_backend.get(id, collection=self.name, filters=filters)

        # Convert ID to UUID if needed
        uuid_id = self._ensure_uuid(id)

        # Independent operation
        try:
            points = self._client.retrieve(
                collection_name=self.name,
                ids=[uuid_id],
                with_payload=True,
                with_vectors=False,
            )

            if not points:
                return None

            point = points[0]
            payload = point.payload or {}

            # Check expiration
            expires_at_str = payload.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if self._is_expired(expires_at):
                    # Delete expired item
                    self._client.delete(
                        collection_name=self.name, points_selector=[uuid_id]
                    )
                    return None

            # Check filters - they are stored as top-level fields in payload
            if filters:
                for key, value in filters.items():
                    if payload.get(key) != value:
                        return None

            return payload.get("value")

        except Exception:
            return None

    def add(
        self,
        entry: Object,
        *,
        id: Optional[str] = None,
        filters: Optional[Filters] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Add an item to the collection."""
        if self._storage_backend is not None:
            # Delegate to storage backend
            self._storage_backend.add(
                entry, id=id, collection=self.name, filters=filters, ttl=ttl
            )
            return

        # Independent operation
        item_id = id or str(uuid.uuid4())
        # Convert to UUID if needed
        uuid_id = self._ensure_uuid(item_id)

        expires_at = self._calculate_expires_at(ttl)
        created_at = datetime.now(timezone.utc)

        # Prepare vector
        vector = self._prepare_vector(entry)

        if len(vector) != self.vector_size:
            raise ValueError(
                f"Vector size {len(vector)} doesn't match collection size {self.vector_size}"
            )

        # Prepare payload - store original ID if converted
        payload = {
            "value": entry,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

        # Add filter fields as top-level payload fields
        if filters:
            for key, value in filters.items():
                payload[key] = value

        # Store original ID if it was converted
        if item_id != uuid_id:
            payload["original_id"] = item_id

        if expires_at:
            payload["expires_at"] = expires_at.isoformat()

        # Store in memory with UUID
        self._items[uuid_id] = payload

        # Create point and upsert to Qdrant
        point = PointStruct(id=uuid_id, vector=vector, payload=payload)

        self._client.upsert(collection_name=self.name, points=[point])

    def query(
        self,
        *,
        filters: Optional[Filters] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Object]:
        """Query items from the collection."""
        if self._storage_backend is not None:
            return self._storage_backend.query(
                collection=self.name,
                filters=filters,
                search=search,
                limit=limit,
            )

        # For basic query without vector search, just return all items with filters
        if search is None:
            return self._query_all(filters=filters, limit=limit)

        # If search is provided but no embedding function, treat as error
        if self._embedding_function is None:
            raise ValueError(
                "Search query provided but no embedding_function configured. "
                "Use vector_search() for direct vector similarity search."
            )

        # Convert search to vector and perform similarity search
        query_vector = self._embedding_function(search)
        return self.vector_search(
            query_vector=query_vector, filters=filters, limit=limit
        )

    def _query_all(
        self,
        *,
        filters: Optional[Filters] = None,
        limit: Optional[int] = None,
    ) -> List[Object]:
        """Query all items with optional filters (no vector search)."""
        try:
            # Scroll through all points
            points, _ = self._client.scroll(
                collection_name=self.name,
                scroll_filter=self._build_qdrant_filter(filters),
                limit=limit or 100,
                with_payload=True,
                with_vectors=False,
            )

            results = []
            for point in points:
                payload = point.payload or {}

                # Check expiration
                expires_at_str = payload.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if self._is_expired(expires_at):
                        continue

                results.append(payload.get("value"))

            return results

        except Exception:
            return []

    def vector_search(
        self,
        query_vector: Union[List[float], np.ndarray],
        *,
        filters: Optional[Filters] = None,
        limit: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Object]:
        """
        Perform vector similarity search.

        Args:
            query_vector: Query vector for similarity search
            filters: Optional filters to apply
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of matching objects sorted by similarity score
        """
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()

        if len(query_vector) != self.vector_size:
            raise ValueError(
                f"Query vector size {len(query_vector)} doesn't match collection size {self.vector_size}"
            )

        try:
            results = self._client.query_points(
                collection_name=self.name,
                query=query_vector,
                query_filter=self._build_qdrant_filter(filters),
                limit=limit or 10,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False,
            )

            matches = []
            for result in results.points:
                payload = result.payload or {}

                # Check expiration
                expires_at_str = payload.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if self._is_expired(expires_at):
                        continue

                matches.append(payload.get("value"))

            return matches

        except Exception:
            return []

    def get_vector(self, id: str) -> Optional[List[float]]:
        """Get the vector for a specific item by ID."""
        # Convert ID to UUID if needed
        uuid_id = self._ensure_uuid(id)

        try:
            points = self._client.retrieve(
                collection_name=self.name,
                ids=[uuid_id],
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

    def delete(self, id: str) -> bool:
        """Delete an item by ID."""
        # Convert ID to UUID if needed
        uuid_id = self._ensure_uuid(id)

        try:
            self._client.delete(collection_name=self.name, points_selector=[uuid_id])
            # Remove from in-memory storage if exists
            self._items.pop(uuid_id, None)
            return True
        except Exception:
            return False

    def count(self, *, filters: Optional[Filters] = None) -> int:
        """Count items in the collection."""
        try:
            info = self._client.count(
                collection_name=self.name,
                count_filter=self._build_qdrant_filter(filters),
                exact=True,
            )
            return info.count
        except Exception:
            return 0

    def attach_to_database(self, database: Any) -> None:
        """Attach this collection to a database instance."""
        self._storage_backend = database
        # Ensure the collection exists in the database
        database.create_collection(
            self.name, schema=self.schema, default_ttl=self.default_ttl
        )
