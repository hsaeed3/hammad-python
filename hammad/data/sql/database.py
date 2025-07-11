"""hammad.data.sql.database"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    Union,
    Literal,
    final,
)
import uuid
import json

try:
    from sqlalchemy import (
        create_engine,
        Column,
        String,
        Text,
        DateTime,
        Integer,
        MetaData,
        Table,
        and_,
        or_,
        select,
        insert,
        update,
        delete,
        Engine,
    )
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.sql import Select

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # SQLAlchemy not available
    SQLALCHEMY_AVAILABLE = False
    create_engine = None
    Engine = None
    Session = None

from .types import (
    DatabaseItemType,
    DatabaseItemFilters,
    DatabaseItem,
    QueryOperator,
    QueryCondition,
    QueryFilter,
)

__all__ = [
    "create_database",
    "Database",
    "DatabaseError",
]


class DatabaseError(Exception):
    """Exception raised when an error occurs in the Database."""


@final
class Database(Generic[DatabaseItemType]):
    """
    A clean SQL-based database implementation using SQLAlchemy that provides
    the lowest-level storage backend for collections.

    Features:
    - Optional schema validation
    - Custom path format support (memory or file-based)
    - Pythonic query interface with type-safe operators
    - TTL support with automatic cleanup
    - JSON serialization for complex objects
    - Transaction support
    """

    def __init__(
        self,
        *,
        name: str = "default",
        schema: Optional[Type[DatabaseItemType]] = None,
        ttl: Optional[int] = None,
        path: Optional[Union[Path, str]] = None,
        table_name: str = "items",
        auto_cleanup_expired: bool = True,
    ) -> None:
        """
        Initialize a new Database instance.

        Args:
            name: The name of the database
            schema: Optional schema type for validation
            ttl: Default time-to-live in seconds
            path: File path for persistent storage (None = in-memory)
            table_name: Name of the primary table
            auto_cleanup_expired: Whether to automatically clean up expired items
        """
        if not SQLALCHEMY_AVAILABLE:
            raise DatabaseError(
                "SQLAlchemy is required for Database. "
                "Install with: pip install sqlalchemy"
            )

        self.name = name
        self.schema = schema
        self.ttl = ttl
        self.path = Path(path) if path else None
        self.table_name = table_name
        self.auto_cleanup_expired = auto_cleanup_expired

        # Initialize SQLAlchemy components
        self._engine: Optional[Engine] = None
        self._session_factory = None
        self._metadata: Optional[MetaData] = None
        self._table: Optional[Table] = None

        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database engine and create tables."""
        # Determine connection string
        if self.path is None:
            # In-memory database
            connection_string = "sqlite:///:memory:"
        else:
            # File-based database
            # Create directory if it doesn't exist
            if self.path.parent != Path("."):
                self.path.parent.mkdir(parents=True, exist_ok=True)
            connection_string = f"sqlite:///{self.path}"

        # Create engine
        self._engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True,
        )

        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)

        # Create metadata and table
        self._metadata = MetaData()
        self._create_table()

    def _create_table(self) -> None:
        """Create the main table for storing items."""
        self._table = Table(
            self.table_name,
            self._metadata,
            Column("id", String, primary_key=True),
            Column("item_data", Text, nullable=False),  # JSON serialized item
            Column("filters", Text),  # JSON serialized filters
            Column("created_at", DateTime, nullable=False),
            Column("updated_at", DateTime, nullable=False),
            Column("ttl", Integer),  # TTL in seconds
            Column("table_name", String, default=self.table_name),
        )

        # Create all tables
        self._metadata.create_all(self._engine)

    def _serialize_item(self, item: DatabaseItemType) -> str:
        """Serialize an item to JSON string."""
        from dataclasses import is_dataclass, asdict

        if isinstance(item, (str, int, float, bool, type(None))):
            return json.dumps(item)
        elif isinstance(item, (list, dict)):
            return json.dumps(item)
        elif is_dataclass(item):
            return json.dumps(asdict(item))
        elif hasattr(item, "__dict__"):
            return json.dumps(item.__dict__)
        else:
            return json.dumps(str(item))

    def _deserialize_item(self, data: str) -> DatabaseItemType:
        """Deserialize an item from JSON string."""
        return json.loads(data)

    def _validate_schema(self, item: DatabaseItemType) -> None:
        """Validate item against schema if one is set."""
        if self.schema is not None:
            if not isinstance(item, self.schema):
                raise ValueError(f"Item is not of type {self.schema.__name__}")

    def _build_query_conditions(
        self,
        query_filter: QueryFilter,
        table: Table,
    ) -> Any:
        """Build SQLAlchemy query conditions from QueryFilter."""
        conditions = []

        for condition in query_filter.conditions:
            column = getattr(table.c, condition.field, None)
            if column is None:
                continue

            if condition.operator == "eq":
                conditions.append(column == condition.value)
            elif condition.operator == "ne":
                conditions.append(column != condition.value)
            elif condition.operator == "gt":
                conditions.append(column > condition.value)
            elif condition.operator == "gte":
                conditions.append(column >= condition.value)
            elif condition.operator == "lt":
                conditions.append(column < condition.value)
            elif condition.operator == "lte":
                conditions.append(column <= condition.value)
            elif condition.operator == "in":
                conditions.append(column.in_(condition.value))
            elif condition.operator == "not_in":
                conditions.append(~column.in_(condition.value))
            elif condition.operator == "like":
                conditions.append(column.like(condition.value))
            elif condition.operator == "ilike":
                conditions.append(column.ilike(condition.value))
            elif condition.operator == "is_null":
                conditions.append(column.is_(None))
            elif condition.operator == "is_not_null":
                conditions.append(column.isnot(None))
            elif condition.operator == "startswith":
                conditions.append(column.like(f"{condition.value}%"))
            elif condition.operator == "endswith":
                conditions.append(column.like(f"%{condition.value}"))
            elif condition.operator == "contains":
                conditions.append(column.like(f"%{condition.value}%"))

        if not conditions:
            return None

        if query_filter.logic == "and":
            return and_(*conditions)
        else:  # or
            return or_(*conditions)

    def _cleanup_expired_items(self, session: Session) -> int:
        """Remove expired items from the database."""
        if not self.auto_cleanup_expired:
            return 0

        now = datetime.now(timezone.utc)

        # Find expired items by checking created_at + ttl < now
        stmt = select(self._table).where(
            and_(
                self._table.c.ttl.isnot(None),
                self._table.c.created_at + (self._table.c.ttl * timedelta(seconds=1))
                < now,
            )
        )

        expired_items = session.execute(stmt).fetchall()
        expired_ids = [item.id for item in expired_items]

        if expired_ids:
            delete_stmt = delete(self._table).where(self._table.c.id.in_(expired_ids))
            session.execute(delete_stmt)

        return len(expired_ids)

    def add(
        self,
        item: DatabaseItemType,
        *,
        id: Optional[str] = None,
        filters: Optional[DatabaseItemFilters] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """
        Add an item to the database.

        Args:
            item: The item to store
            id: Optional ID (will generate UUID if not provided)
            filters: Optional filters/metadata
            ttl: Optional TTL in seconds

        Returns:
            The ID of the stored item
        """
        self._validate_schema(item)

        item_id = id or str(uuid.uuid4())
        item_ttl = ttl or self.ttl
        now = datetime.now(timezone.utc)

        serialized_item = self._serialize_item(item)
        serialized_filters = json.dumps(filters or {})

        with self._session_factory() as session:
            # Check if item already exists
            existing = session.execute(
                select(self._table).where(self._table.c.id == item_id)
            ).fetchone()

            if existing:
                # Update existing item
                stmt = (
                    update(self._table)
                    .where(self._table.c.id == item_id)
                    .values(
                        item_data=serialized_item,
                        filters=serialized_filters,
                        updated_at=now,
                        ttl=item_ttl,
                    )
                )
            else:
                # Insert new item
                stmt = insert(self._table).values(
                    id=item_id,
                    item_data=serialized_item,
                    filters=serialized_filters,
                    created_at=now,
                    updated_at=now,
                    ttl=item_ttl,
                    table_name=self.table_name,
                )

            session.execute(stmt)

            # Cleanup expired items
            self._cleanup_expired_items(session)

            session.commit()

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
            id: The item ID
            filters: Optional filters to match

        Returns:
            The database item or None if not found
        """
        with self._session_factory() as session:
            stmt = select(self._table).where(self._table.c.id == id)
            result = session.execute(stmt).fetchone()

            if not result:
                return None

            # Check if expired
            if result.ttl is not None:
                expires_at = result.created_at + timedelta(seconds=result.ttl)
                if datetime.now(timezone.utc) >= expires_at:
                    # Delete expired item
                    session.execute(delete(self._table).where(self._table.c.id == id))
                    session.commit()
                    return None

            # Check filters if provided
            if filters:
                stored_filters = json.loads(result.filters or "{}")
                if not all(stored_filters.get(k) == v for k, v in filters.items()):
                    return None

            # Deserialize and return
            item_data = self._deserialize_item(result.item_data)
            stored_filters = json.loads(result.filters or "{}")

            return DatabaseItem(
                id=result.id,
                item=item_data,
                created_at=result.created_at,
                updated_at=result.updated_at,
                ttl=result.ttl,
                filters=stored_filters,
                table_name=result.table_name,
            )

    def query(
        self,
        query_filter: Optional[QueryFilter] = None,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        ascending: bool = True,
    ) -> List[DatabaseItem[DatabaseItemType]]:
        """
        Query items from the database.

        Args:
            query_filter: Filter conditions to apply
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            ascending: Sort direction

        Returns:
            List of matching database items
        """
        with self._session_factory() as session:
            # Cleanup expired items first
            self._cleanup_expired_items(session)

            stmt = select(self._table)

            # Apply filters
            if query_filter:
                conditions = self._build_query_conditions(query_filter, self._table)
                if conditions is not None:
                    stmt = stmt.where(conditions)

            # Apply ordering
            if order_by:
                column = getattr(self._table.c, order_by, None)
                if column is not None:
                    if ascending:
                        stmt = stmt.order_by(column.asc())
                    else:
                        stmt = stmt.order_by(column.desc())
            else:
                # Default order by created_at desc
                stmt = stmt.order_by(self._table.c.created_at.desc())

            # Apply pagination
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            results = session.execute(stmt).fetchall()

            items = []
            for result in results:
                # Double-check expiration (in case of race conditions)
                if result.ttl is not None:
                    expires_at = result.created_at + timedelta(seconds=result.ttl)
                    if datetime.now(timezone.utc) >= expires_at:
                        continue

                item_data = self._deserialize_item(result.item_data)
                stored_filters = json.loads(result.filters or "{}")

                items.append(
                    DatabaseItem(
                        id=result.id,
                        item=item_data,
                        created_at=result.created_at,
                        updated_at=result.updated_at,
                        ttl=result.ttl,
                        filters=stored_filters,
                        table_name=result.table_name,
                    )
                )

            return items

    def delete(self, id: str) -> bool:
        """
        Delete an item by ID.

        Args:
            id: The item ID

        Returns:
            True if item was deleted, False if not found
        """
        with self._session_factory() as session:
            stmt = delete(self._table).where(self._table.c.id == id)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount > 0

    def count(
        self,
        query_filter: Optional[QueryFilter] = None,
    ) -> int:
        """
        Count items matching the filter.

        Args:
            query_filter: Filter conditions to apply

        Returns:
            Number of matching items
        """
        with self._session_factory() as session:
            # Cleanup expired items first
            self._cleanup_expired_items(session)

            from sqlalchemy import func

            stmt = select(func.count(self._table.c.id))

            if query_filter:
                conditions = self._build_query_conditions(query_filter, self._table)
                if conditions is not None:
                    stmt = stmt.where(conditions)

            result = session.execute(stmt).fetchone()
            return result[0] if result else 0

    def clear(self) -> int:
        """
        Clear all items from the database.

        Returns:
            Number of items deleted
        """
        with self._session_factory() as session:
            stmt = delete(self._table)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount

    def cleanup_expired(self) -> int:
        """
        Manually cleanup expired items.

        Returns:
            Number of items cleaned up
        """
        with self._session_factory() as session:
            count = self._cleanup_expired_items(session)
            session.commit()
            return count

    def __repr__(self) -> str:
        """String representation of the database."""
        location = str(self.path) if self.path else "memory"
        return f"<Database name='{self.name}' location='{location}' table='{self.table_name}'>"


def create_database(
    name: str,
    *,
    schema: Optional[Type[DatabaseItemType]] = None,
    ttl: Optional[int] = None,
    path: Optional[Union[Path, str]] = None,
    table_name: str = "items",
    auto_cleanup_expired: bool = True,
) -> Database[DatabaseItemType]:
    """
    Create a new database instance.

    Args:
        name: The name of the database
        schema: Optional schema type for validation
        ttl: Default time-to-live in seconds
        path: File path for storage (None = in-memory)
        table_name: Name of the primary table
        auto_cleanup_expired: Whether to automatically clean up expired items

    Returns:
        A Database instance
    """
    return Database(
        name=name,
        schema=schema,
        ttl=ttl,
        path=path,
        table_name=table_name,
        auto_cleanup_expired=auto_cleanup_expired,
    )
