"""hammad.data.collections.base_collection"""

from typing import Any, Dict, Optional, List, TypeVar, Union, Type, Generic
from abc import ABC, abstractmethod

__all__ = (
    "BaseCollection",
    "Object",
    "Filters",
    "Schema",
)


Object = TypeVar("Object")
"""Represents an object that can be stored within a collection."""


Filters = Dict[str, object]
"""Represents a dictionary of filters that can be applied to objects within
a collection."""


Schema = Union[Type[Any], Dict[str, Any], None]
"""Represents a strict schema that a collection can optionally enforce."""


class BaseCollection(ABC, Generic[Object]):
    """Base class defining the interface for collections. This
    class does not provide any functionality.
    """

    @abstractmethod
    def get(self, id: str, *, filters: Optional[Filters] = None) -> Optional[Any]:
        """Get an item by ID."""
        pass

    @abstractmethod
    def add(
        self,
        entry: Any,
        *,
        id: Optional[str] = None,
        filters: Optional[Filters] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Add an item to the collection."""
        pass

    @abstractmethod
    def query(
        self,
        *,
        filters: Optional[Filters] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Query items from the collection."""
        pass
