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
from ..collections.collection import (
    create_collection,
    SearchableCollectionSettings,
    VectorCollectionSettings,
)

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
        tantivy_settings: Optional[SearchableCollectionSettings] = None,
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
        qdrant_settings: Optional[VectorCollectionSettings] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
    ) -> "VectorCollection[DatabaseEntryType]":
        """Create a vector collection using Qdrant for semantic similarity search."""
        ...

    def create_searchable_collection(
        self,
        name: str,
        *,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        tantivy_settings: Optional[SearchableCollectionSettings] = None,
    ) -> "SearchableCollection[DatabaseEntryType]":
        """Create a searchable collection using tantivy for full-text search."""
        collection = create_collection(
            "searchable",
            name,
            schema=schema,
            default_ttl=default_ttl or self.default_ttl,
            storage_backend=self,
            tantivy_settings=tantivy_settings,
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
        qdrant_settings: Optional[VectorCollectionSettings] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
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
            qdrant_settings=qdrant_settings,
            embedding_function=embedding_function,
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
