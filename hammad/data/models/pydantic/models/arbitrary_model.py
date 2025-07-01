"""hammad.data.models.pydantic.models.arbitrary_model"""

from typing import Any, Dict
from pydantic import ConfigDict

from .subscriptable_model import SubscriptableModel

__all__ = ("ArbitraryModel",)


class ArbitraryModel(SubscriptableModel):
    """
    A model that allows dynamic field assignment and access.
    Perfect for handling arbitrary JSON data or when schema is unknown at compile time.

    Usage:
        >>> data = ArbitraryModel()
        >>> data.name = "John"
        >>> data.age = 30
        >>> data.metadata = {"key": "value"}
        >>> print(data.name)  # John
        >>> print(data["age"])  # 30
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Store extra fields for easy access
        self._arbitrary_fields: Dict[str, Any] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in self.__class__.model_fields:
            super().__setattr__(name, value)
        else:
            # Store in dynamic fields and set normally
            if hasattr(self, "_arbitrary_fields"):
                self._arbitrary_fields[name] = value
            super().__setattr__(name, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including all dynamic fields."""
        result = self.model_dump()
        if hasattr(self, "_arbitrary_fields"):
            result.update(self._arbitrary_fields)
        return result
