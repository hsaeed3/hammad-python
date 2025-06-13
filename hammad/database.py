"""hammad.database

Contains the `Database` class, which is an incredibly simple to use
wrapper over various modules from the `sqlalchemy` library, which allows
for the creation of a simple, yet powerful database interface.
"""

import uuid
import json
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import (
    Any,
    Dict,
    Optional,
    List,
    Iterator,
    Literal,
    Tuple,
    Type,
    TypeVar,
    Generic,
    TypeAlias,
    Union,
    cast,
)
import threading

from sqlalchemy import (
    create_engine,
    Engine,
    event,
    pool,
    Column,
    String,
    DateTime,
    Integer,
    JSON as SQLAlchemyJSON,
    MetaData,
    and_,
)
from sqlalchemy.orm import Session as SQLAlchemySession, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from .logger import get_logger


logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------


DatabaseLocation: TypeAlias = Literal[
    "memory",
    "disk",
]
"""The location to initialize or load a database from. The `hammad` definition
of a database is quite literal, and does not mean anything more than a persistable
collection of data items. Concepts like queries, transactions, and other 
functional database concepts are not supported, as they are not the focus of this
library."""


DatabaseEntryType = TypeVar("DatabaseEntryType", bound=BaseModel | Dict | Any)
"""Helper type variable for input objects added to a database."""


DatabaseSchema: TypeAlias = Union[
    Type[DatabaseEntryType], Type[BaseModel], Dict[str, Any], None
]
"""An optional schema type that a database must follow for a specific collection
of data items. Databases are built around `collections`, and a single collection can
adhere to a schema, or not."""


DatabaseCollection: TypeAlias = Union[Literal["default"], str]
"""Helper type alias that provides common names for a collection within 
a database. Only the `default` collection is created automatically, if no
section name is provided when adding objects."""


DatabaseFilters: TypeAlias = Dict[str, str | int | float | bool | None]
"""Alias for a filter that can be used to create even more easy 'complexity' within a 
database. When adding items to a database, you can specify something like

```python
database.add(
    ...,
    filter = {
        "some_key" : "some_value",
        "some_other_key" : 123,
        "some_third_key" : True,
        "some_fourth_key" : None,
    }
)
"""


_DatabaseEntry = declarative_base()


class DatabaseEntry(_DatabaseEntry):
    """
    Base class definition for an data item within a database or
    a collection. This class is used to define both the strictly
    schema defined, and standard key-value data item types used within
    hammad.
    """

    __tablename__: str
    __tablename__ = "database_entries"
    __table_args__ = {"extend_existing": True}

    id: Column[str] = Column(String(255), primary_key=True, index=True)
    """
    The ID of the data item.
    """
    value: Column[DatabaseEntryType] = Column(SQLAlchemyJSON, nullable=False)
    """
    The value of an data item.
    """
    collection: Column[str] = Column(String(255), default="default", index=True)
    """
    The collection that the data item belongs to.
    """
    filters: Column[DatabaseFilters] = Column(SQLAlchemyJSON, nullable=True)
    """
    Any additional filters that belong to this data item.
    """
    created_at: Column[datetime] = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    """
    The timestamp of when the data item was created.
    """
    updated_at: Column[datetime] = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    """
    The timestamp of when the data item was last updated.
    """
    expires_at: Column[datetime] = Column(DateTime, nullable=True, index=True)
    """
    The timestamp of when the data item will expire.
    """

    def __repr__(self) -> str:
        return f"<DatabaseEntry id={self.id} collection={self.collection}>"


# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------


class Database(Generic[DatabaseEntryType]):
    """
    A simple, yet powerful database interface that allows for the creation of
    a database that can be used to store and retrieve data items.
    """

    def __init__(
        self,
        location: DatabaseLocation = "memory",
        *,
        default_ttl: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Creates a new database.

        Args:
            location (DatabaseLocation, optional): The location to initialize or load a database from. Defaults to "memory".
            default_ttl (Optional[int], optional): The default TTL for items in the database. Defaults to None.
            verbose (bool, optional): Whether to log verbose information. Defaults to False.
        """
        self.location = location
        self.default_ttl = default_ttl
        self.verbose = verbose

        # Thread-safety for in-memory operations
        self._lock = threading.Lock()

        # Per-collection metadata
        self._schemas: Dict[str, Optional[DatabaseSchema]] = {}
        self._collection_ttls: Dict[str, Optional[int]] = {}

        # In-memory store → {collection: {id: item_dict}}
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {"default": {}}

        # Engine for on-disk mode
        self._engine: Optional[Engine] = None
        if self.location == "disk":
            db_url = "sqlite:///./hammad_database.db"
            self._engine = create_engine(
                db_url,
                echo=self.verbose,
                future=True,
                connect_args={"check_same_thread": False},
                poolclass=pool.StaticPool,
            )
            _DatabaseEntry.metadata.create_all(self._engine, checkfirst=True)

        if self.verbose:
            logger.info(f"Database initialised ({self.location}).")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_expires_at(
        self, ttl: Optional[int], collection: str
    ) -> Optional[datetime]:
        """Return an absolute expiry time for the given TTL (seconds)."""
        if ttl is None:
            ttl = self._collection_ttls.get(collection) or self.default_ttl
        if ttl and ttl > 0:
            return datetime.now(timezone.utc) + timedelta(seconds=ttl)
        return None

    def _is_expired(self, expires_at: Optional[datetime]) -> bool:
        if expires_at is None:
            return False

        now = datetime.now(timezone.utc)
        # Handle both timezone-aware and naive datetimes
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return now >= expires_at

    def _match_filters(
        self, stored: Optional[DatabaseFilters], query: Optional[DatabaseFilters]
    ) -> bool:
        if query is None:
            return True
        if stored is None:
            return False
        return all(stored.get(k) == v for k, v in query.items())

    def _serialize_item(self, item: Any, schema: Optional[DatabaseSchema]) -> Any:
        if schema is None:
            return item
        if hasattr(item, "__dataclass_fields__"):
            return asdict(item)
        if hasattr(item, "model_dump"):
            return item.model_dump()
        if isinstance(item, dict):
            return item
        raise TypeError(
            f"Cannot serialize item of type {type(item)} for schema storage"
        )

    def _deserialize_item(self, data: Any, schema: Optional[DatabaseSchema]) -> Any:
        if schema is None or isinstance(schema, dict):
            return data
        try:
            if hasattr(schema, "model_validate"):
                return schema.model_validate(data)
            return schema(**data)  # type: ignore[arg-type]
        except Exception:
            return data

    @contextmanager
    def _get_session(self) -> Iterator[SQLAlchemySession]:
        if self.location != "disk" or self._engine is None:
            raise RuntimeError(
                "A SQLAlchemy session is only available when using disk storage."
            )
        session = SQLAlchemySession(self._engine)
        try:
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def _ensure_collection(
        self,
        name: str,
        schema: Optional[DatabaseSchema] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Create a collection if it doesn't yet exist, honouring schema consistency."""
        with self._lock:
            if name in self._schemas:
                if schema is not None and self._schemas[name] != schema:
                    raise TypeError(
                        f"Collection '{name}' already exists with a different schema."
                    )
                return
            self._schemas[name] = schema
            self._collection_ttls[name] = default_ttl
            self._storage.setdefault(name, {})
            if self.verbose:
                logger.debug(f"Created collection '{name}' (ttl={default_ttl})")

    def create_collection(
        self,
        name: str,
        schema: Optional[DatabaseSchema] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """
        Creates a new collection within the database.
        """
        self._ensure_collection(name, schema=schema, default_ttl=default_ttl)

    def add(
        self,
        entry: DatabaseEntryType | Any,
        *,
        id: Optional[str] = None,
        collection: DatabaseCollection = "default",
        filters: Optional[DatabaseFilters] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Add an item to the database using an optional ID (key) to a specified
        collection.

        Example:
            ```python
            database.add(
                entry = {
                    "name" : "John Doe",
                },
                filters = {
                    "user_group" : "admin",
                    "is_active" : True,
                }
            )
            ```

        Args:
            entry (DatabaseEntryType | Any): The item to add to the database.
            id (Optional[str], optional): The ID of the item. Defaults to None.
            collection (DatabaseCollection, optional): The collection to add the item to. Defaults to "default".
            filters (Optional[DatabaseFilters], optional): Any additional filters to apply to the item. Defaults to None.
            ttl (Optional[int], optional): The TTL for the item. Defaults to None.
        """
        self._ensure_collection(collection)
        schema = self._schemas.get(collection)

        item_id = id or str(uuid.uuid4())
        expires_at = self._calculate_expires_at(ttl, collection)
        serialized_value = self._serialize_item(entry, schema)

        if self.location == "memory":
            with self._lock:
                coll_store = self._storage.setdefault(collection, {})
                coll_store[item_id] = {
                    "value": entry,
                    "serialized": serialized_value,
                    "filters": filters or {},
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "expires_at": expires_at,
                }
        else:  # disk
            with self._get_session() as session:
                row = (
                    session.query(DatabaseEntry)
                    .filter_by(id=item_id, collection=collection)
                    .first()
                )
                if row:
                    row.value = serialized_value
                    row.filters = filters or {}
                    row.updated_at = datetime.now(timezone.utc)
                    row.expires_at = expires_at
                else:
                    session.add(
                        DatabaseEntry(
                            id=item_id,
                            collection=collection,
                            value=serialized_value,
                            filters=filters or {},
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                            expires_at=expires_at,
                        )
                    )

    def get(
        self,
        id: str,
        *,
        collection: DatabaseCollection = "default",
        filters: Optional[DatabaseFilters] = None,
    ) -> Optional[DatabaseEntryType]:
        """Get an item from the database using an optional ID (key) to a specified
        collection.

        """
        # For memory databases, collection must exist in schemas
        if self.location == "memory" and collection not in self._schemas:
            return None

        schema = self._schemas.get(collection)

        if self.location == "memory":
            coll_store = self._storage.get(collection, {})
            item = coll_store.get(id)
            if not item:
                return None
            if self._is_expired(item["expires_at"]):
                with self._lock:
                    del coll_store[id]
                return None
            if not self._match_filters(item.get("filters"), filters):
                return None
            return (
                item["value"]
                if schema is None
                else self._deserialize_item(item["serialized"], schema)
            )
        else:
            # For disk databases, ensure collection is tracked if we find data
            with self._get_session() as session:
                row = (
                    session.query(DatabaseEntry)
                    .filter_by(id=id, collection=collection)
                    .first()
                )
                if not row:
                    return None

                # Auto-register collection if found on disk but not in memory
                if collection not in self._schemas:
                    self._ensure_collection(collection)
                    schema = self._schemas.get(collection)

                if self._is_expired(row.expires_at):
                    session.delete(row)
                    return None
                if not self._match_filters(row.filters, filters):
                    return None
                return self._deserialize_item(row.value, schema)
