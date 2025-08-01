"""hammad.data.sql.types"""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    TypeAlias,
    Literal,
    Union,
)
import uuid

__all__ = (
    "DatabaseItemType",
    "DatabaseItemFilters",
    "DatabaseItem",
    "QueryOperator",
    "QueryCondition",
    "QueryFilter",
)


DatabaseItemType = TypeVar("DatabaseItemType")
"""Generic type variable for any valid item type that can be stored
within a database."""


DatabaseItemFilters: TypeAlias = Dict[str, object]
"""A dictionary of filters that can be used to query the database."""


QueryOperator = Literal[
    "eq",  # equal
    "ne",  # not equal
    "gt",  # greater than
    "gte",  # greater than or equal
    "lt",  # less than
    "lte",  # less than or equal
    "in",  # in list
    "not_in",  # not in list
    "like",  # SQL LIKE
    "ilike",  # case insensitive LIKE
    "is_null",  # IS NULL
    "is_not_null",  # IS NOT NULL
    "contains",  # for JSON contains
    "startswith",  # string starts with
    "endswith",  # string ends with
]
"""Supported query operators for database queries."""


@dataclass
class QueryCondition:
    """Represents a single query condition for database filtering."""

    field: str
    """The field name to filter on."""

    operator: QueryOperator
    """The operator to use for comparison."""

    value: Any = None
    """The value to compare against (not needed for is_null/is_not_null)."""


@dataclass
class QueryFilter:
    """Represents a collection of query conditions with logical operators."""

    conditions: list[QueryCondition] = field(default_factory=list)
    """List of individual query conditions."""

    logic: Literal["and", "or"] = "and"
    """Logical operator to combine conditions."""


@dataclass
class DatabaseItem(Generic[DatabaseItemType]):
    """Base class for all items that can be stored within a database."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """The unique identifier for this item."""

    item: DatabaseItemType = field(default_factory=lambda: None)
    """The item that is stored within this database item."""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """The timestamp when this item was created."""

    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """The timestamp when this item was last updated."""

    ttl: Optional[int] = field(default=None)
    """The time to live for this item in seconds."""

    filters: DatabaseItemFilters = field(default_factory=dict)
    """The filters that are associated with this item."""

    table_name: str = field(default="default")
    """The table/collection name where this item is stored."""

    score: Optional[float] = field(default=None)
    """The similarity score for this item (used in vector search results)."""

    def is_expired(self) -> bool:
        """Check if this item has expired based on its TTL."""
        if self.ttl is None:
            return False

        from datetime import timedelta

        expires_at = self.created_at + timedelta(seconds=self.ttl)
        return datetime.now(timezone.utc) >= expires_at

    def expires_at(self) -> Optional[datetime]:
        """Calculate when this item will expire."""
        if self.ttl is None:
            return None

        from datetime import timedelta

        return self.created_at + timedelta(seconds=self.ttl)
