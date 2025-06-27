"""hammad.data.databases.database"""

import uuid
from typing import (
    Any,
    Dict,
    Optional,
    List,
    TypeVar,
    Generic,
    Callable,
    overload,
    Literal,
    TYPE_CHECKING,
)
from datetime import datetime, timezone, timedelta

from ..collections.base_collection import BaseCollection, Filters, Schema
from ..collections.collection import create_collection

if TYPE_CHECKING:
    from ..collections.searchable_collection import SearchableCollection
    from ..collections.vector_collection import VectorCollection

__all__ = ("Database",)

DatabaseEntryType = TypeVar("DatabaseEntryType", bound=Any)


class Database(Generic[DatabaseEntryType]):
    """
    Enhanced Database class that supports both traditional collections and
    new searchable/vector collections with beautiful IDE typing support.

    Features:
    - Dict-like access: db["collection_name"]
    - Easy creation of searchable and vector collections
    - Full type hinting and IDE autocomplete
    - Backward compatibility with traditional collections
    - TTL support and filtering
    """

    def __init__(self, location: str = "memory", default_ttl: Optional[int] = None):
        """
        Initialize the database.

        Args:
            location: Storage location ("memory" for in-memory, or path for persistent)
            default_ttl: Default TTL for items in seconds
        """
        self.location = location
        self.default_ttl = default_ttl

        # Storage for traditional collections
        self._schemas: Dict[str, Optional[Schema]] = {}
        self._collection_ttls: Dict[str, Optional[int]] = {}
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {"default": {}}

        # Registry for modern collections (searchable/vector)
        self._collections: Dict[str, BaseCollection] = {}

    def __repr__(self) -> str:
        all_collections = set(self._schemas.keys()) | set(self._collections.keys())
        return (
            f"<Database location='{self.location}' collections={list(all_collections)}>"
        )

    @overload
    def create_searchable_collection(
        self,
        name: str,
        *,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        heap_size: Optional[int] = None,
        num_threads: Optional[int] = None,
        index_path: Optional[str] = None,
        schema_builder: Optional[Any] = None,
        writer_memory: Optional[int] = None,
        reload_policy: Optional[str] = None,
    ) -> "SearchableCollection[DatabaseEntryType]":
        """Create a searchable collection using tantivy for full-text search."""
        ...

    @overload
    def create_vector_collection(
        self,
        name: str,
        vector_size: int,
        *,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        distance_metric: Optional[Any] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
        path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        prefer_grpc: Optional[bool] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> "VectorCollection[DatabaseEntryType]":
        """Create a vector collection using Qdrant for semantic similarity search."""
        ...

    def create_searchable_collection(
        self,
        name: str,
        *,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        heap_size: Optional[int] = None,
        num_threads: Optional[int] = None,
        index_path: Optional[str] = None,
        schema_builder: Optional[Any] = None,
        writer_memory: Optional[int] = None,
        reload_policy: Optional[str] = None,
    ) -> "SearchableCollection[DatabaseEntryType]":
        """Create a searchable collection using tantivy for full-text search."""
        collection = create_collection(
            "searchable",
            name,
            schema=schema,
            default_ttl=default_ttl or self.default_ttl,
            storage_backend=self,
            heap_size=heap_size,
            num_threads=num_threads,
            index_path=index_path,
            schema_builder=schema_builder,
            writer_memory=writer_memory,
            reload_policy=reload_policy,
        )
        self._collections[name] = collection
        return collection

    def create_vector_collection(
        self,
        name: str,
        vector_size: int,
        *,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        distance_metric: Optional[Any] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
        path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        prefer_grpc: Optional[bool] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> "VectorCollection[DatabaseEntryType]":
        """Create a vector collection using Qdrant for semantic similarity search."""
        collection = create_collection(
            "vector",
            name,
            vector_size,
            schema=schema,
            default_ttl=default_ttl or self.default_ttl,
            storage_backend=self,
            distance_metric=distance_metric,
            embedding_function=embedding_function,
            path=path,
            host=host,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            api_key=api_key,
            timeout=timeout,
        )
        self._collections[name] = collection
        return collection

    def register_collection(self, collection: BaseCollection) -> None:
        """Register an external collection with this database."""
        collection.attach_to_database(self)
        self._collections[collection.name] = collection

    def create_collection(
        self,
        name: str,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Create a traditional collection (backward compatibility)."""
        self._schemas[name] = schema
        self._collection_ttls[name] = default_ttl
        self._storage.setdefault(name, {})

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

    def get(
        self,
        id: str,
        *,
        collection: str = "default",
        filters: Optional[Filters] = None,
    ) -> Optional[DatabaseEntryType]:
        """Get an item from any collection."""
        # Check modern collections first
        if collection in self._collections:
            coll = self._collections[collection]
            # Temporarily remove storage backend to avoid recursion
            original_backend = coll._storage_backend
            coll._storage_backend = None
            try:
                return coll.get(id, filters=filters)
            finally:
                coll._storage_backend = original_backend

        # Traditional collection logic
        if collection not in self._schemas:
            return None

        coll_store = self._storage.get(collection, {})
        item = coll_store.get(id)
        if not item:
            return None

        # Check expiration
        if self._is_expired(item.get("expires_at")):
            del coll_store[id]
            return None

        # Check filters
        if not self._match_filters(item.get("filters"), filters):
            return None

        return item["value"]

    def add(
        self,
        entry: DatabaseEntryType,
        *,
        id: Optional[str] = None,
        collection: str = "default",
        filters: Optional[Filters] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Add an item to any collection."""
        # Check modern collections first
        if collection in self._collections:
            coll = self._collections[collection]
            # Temporarily remove storage backend to avoid recursion
            original_backend = coll._storage_backend
            coll._storage_backend = None
            try:
                coll.add(entry, id=id, filters=filters, ttl=ttl)
            finally:
                coll._storage_backend = original_backend
            return

        # Traditional collection logic
        if collection not in self._schemas:
            self.create_collection(collection)

        item_id = id or str(uuid.uuid4())
        expires_at = self._calculate_expires_at(ttl)
        coll_store = self._storage.setdefault(collection, {})

        coll_store[item_id] = {
            "value": entry,
            "filters": filters or {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }

    def query(
        self,
        *,
        collection: str = "default",
        filters: Optional[Filters] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[DatabaseEntryType]:
        """Query items from any collection."""
        # Check modern collections first
        if collection in self._collections:
            coll = self._collections[collection]
            # Temporarily remove storage backend to avoid recursion
            original_backend = coll._storage_backend
            coll._storage_backend = None
            try:
                return coll.query(filters=filters, search=search, limit=limit, **kwargs)
            finally:
                coll._storage_backend = original_backend

        # Traditional collection logic
        if collection not in self._schemas:
            return []

        results = []
        coll_store = self._storage.get(collection, {})

        for item in coll_store.values():
            # Check expiration
            if self._is_expired(item.get("expires_at")):
                continue

            # Check filters
            if not self._match_filters(item.get("filters"), filters):
                continue

            # Basic search implementation
            if search:
                item_text = str(item["value"]).lower()
                if search.lower() not in item_text:
                    continue

            results.append(item["value"])
            if limit and len(results) >= limit:
                break

        return results

    def __getitem__(self, collection_name: str) -> BaseCollection[DatabaseEntryType]:
        """Get a collection accessor with full IDE typing support."""
        # Return modern collection if it exists
        if collection_name in self._collections:
            return self._collections[collection_name]

        # Create a database-backed collection accessor for traditional collections
        class DatabaseCollectionAccessor(BaseCollection[DatabaseEntryType]):
            def __init__(self, database_instance: "Database", name: str):
                self._database = database_instance
                self.name = name
                self._storage_backend = database_instance

            def get(
                self, id: str, *, filters: Optional[Filters] = None
            ) -> Optional[DatabaseEntryType]:
                return self._database.get(id, collection=self.name, filters=filters)

            def add(
                self,
                entry: DatabaseEntryType,
                *,
                id: Optional[str] = None,
                filters: Optional[Filters] = None,
                ttl: Optional[int] = None,
            ) -> None:
                self._database.add(
                    entry, id=id, collection=self.name, filters=filters, ttl=ttl
                )

            def query(
                self,
                *,
                filters: Optional[Filters] = None,
                search: Optional[str] = None,
                limit: Optional[int] = None,
            ) -> List[DatabaseEntryType]:
                return self._database.query(
                    collection=self.name, filters=filters, search=search, limit=limit
                )

        return DatabaseCollectionAccessor(self, collection_name)

    def __contains__(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        return collection_name in self._schemas or collection_name in self._collections

    def keys(self) -> List[str]:
        """Get all collection names."""
        all_collections = set(self._schemas.keys())
        all_collections.update(self._collections.keys())
        return list(all_collections)

    def collections(self) -> Dict[str, BaseCollection]:
        """Get all modern collections."""
        return self._collections.copy()

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        deleted = False

        if name in self._collections:
            del self._collections[name]
            deleted = True

        if name in self._schemas:
            del self._schemas[name]
            del self._collection_ttls[name]
            if name in self._storage:
                del self._storage[name]
            deleted = True

        return deleted

    def clear(self) -> None:
        """Clear all collections and data."""
        self._collections.clear()
        self._schemas.clear()
        self._collection_ttls.clear()
        self._storage.clear()
        self._storage["default"] = {}


@overload
def create_database(
    type: Literal["searchable"],
    location: str = "memory",
    *,
    default_ttl: Optional[int] = None,
    heap_size: Optional[int] = None,
    num_threads: Optional[int] = None,
    index_path: Optional[str] = None,
    schema_builder: Optional[Any] = None,
    writer_memory: Optional[int] = None,
    reload_policy: Optional[str] = None,
) -> "Database[SearchableCollection]": ...


@overload
def create_database(
    type: Literal["vector"],
    location: str = "memory",
    *,
    default_ttl: Optional[int] = None,
    path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    grpc_port: Optional[int] = None,
    prefer_grpc: Optional[bool] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> "Database[VectorCollection]": ...


def create_database(
    type: Literal["searchable", "vector"],
    location: str = "memory",
    *,
    default_ttl: Optional[int] = None,
    # Tantivy parameters (searchable databases only)
    heap_size: Optional[int] = None,
    num_threads: Optional[int] = None,
    index_path: Optional[str] = None,
    schema_builder: Optional[Any] = None,
    writer_memory: Optional[int] = None,
    reload_policy: Optional[str] = None,
    # Qdrant parameters (vector databases only)
    path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    grpc_port: Optional[int] = None,
    prefer_grpc: Optional[bool] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> "Database":
    """
    Create a database instance optimized for specific collection types.

    Args:
        type: Type of database to create ("searchable" or "vector")
        location: Database location (default: "memory")
        default_ttl: Default TTL for items in seconds

        Tantivy parameters (searchable databases only):
        heap_size: Memory allocation for tantivy heap
        num_threads: Number of threads for tantivy operations
        index_path: Path to store tantivy index files
        schema_builder: Custom schema builder for tantivy
        writer_memory: Memory allocation for tantivy writer
        reload_policy: Policy for reloading tantivy index

        Qdrant parameters (vector databases only):
        path: Path for local Qdrant storage
        host: Qdrant server host
        port: Qdrant server port
        grpc_port: Qdrant gRPC port
        prefer_grpc: Whether to prefer gRPC over HTTP
        api_key: API key for Qdrant authentication
        timeout: Request timeout for Qdrant operations

    Returns:
        A Database instance optimized for the specified collection type
    """
    database = Database(location=location, default_ttl=default_ttl)

    # Store the database type for future collection creation optimization
    database._database_type = type

    if type == "searchable":
        # Build default tantivy settings from individual parameters
        tantivy_defaults = {}
        if heap_size is not None:
            tantivy_defaults["heap_size"] = heap_size
        if num_threads is not None:
            tantivy_defaults["num_threads"] = num_threads
        if index_path is not None:
            tantivy_defaults["index_path"] = index_path
        if schema_builder is not None:
            tantivy_defaults["schema_builder"] = schema_builder
        if writer_memory is not None:
            tantivy_defaults["writer_memory"] = writer_memory
        if reload_policy is not None:
            tantivy_defaults["reload_policy"] = reload_policy

        if tantivy_defaults:
            database._default_tantivy_settings = tantivy_defaults

    elif type == "vector":
        # Build default qdrant settings from individual parameters
        qdrant_defaults = {}
        if path is not None:
            qdrant_defaults["path"] = path
        if host is not None:
            qdrant_defaults["host"] = host
        if port is not None:
            qdrant_defaults["port"] = port
        if grpc_port is not None:
            qdrant_defaults["grpc_port"] = grpc_port
        if prefer_grpc is not None:
            qdrant_defaults["prefer_grpc"] = prefer_grpc
        if api_key is not None:
            qdrant_defaults["api_key"] = api_key
        if timeout is not None:
            qdrant_defaults["timeout"] = timeout

        if qdrant_defaults:
            database._default_qdrant_settings = qdrant_defaults

    return database
