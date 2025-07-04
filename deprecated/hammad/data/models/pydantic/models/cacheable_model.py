"""hammad.data.models.pydantic.models.cacheable_model"""

from typing import Any, Callable, Dict, Optional
from functools import wraps

from .subscriptable_model import SubscriptableModel

__all__ = ("CacheableModel",)


class CacheableModel(SubscriptableModel):
    """
    A model with built-in caching for computed properties.
    Automatically caches expensive computations and invalidates when dependencies change.

    Usage:
        >>> class MyModel(CacheableModel):
        ...     value: int
        ...     @CacheableModel.cached_property(dependencies=["value"])
        ...     def expensive_computation(self) -> int:
        ...         return self.value ** 2
        >>> model = MyModel(value=10)
        >>> model.expensive_computation  # Computed once
        >>> model.expensive_computation  # Returns cached value
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._cache: Dict[str, Any] = {}
        self._cache_dependencies: Dict[str, list] = {}

    @classmethod
    def cached_property(cls, dependencies: Optional[list] = None):
        """Decorator for creating cached properties with optional dependencies."""

        def decorator(func: Callable) -> property:
            prop_name = func.__name__
            deps = dependencies or []

            @wraps(func)
            def wrapper(self) -> Any:
                # Check if cached and dependencies haven't changed
                if prop_name in self._cache:
                    if not deps or all(
                        getattr(self, dep) == self._cache.get(f"_{dep}_snapshot")
                        for dep in deps
                    ):
                        return self._cache[prop_name]

                # Compute and cache
                result = func(self)
                self._cache[prop_name] = result

                # Store dependency snapshots
                for dep in deps:
                    self._cache[f"_{dep}_snapshot"] = getattr(self, dep)

                return result

            return property(wrapper)

        return decorator

    def clear_cache(self, property_name: Optional[str] = None) -> None:
        """Clear cache for specific property or all cached properties."""
        if property_name:
            self._cache.pop(property_name, None)
        else:
            self._cache.clear()

    def __setattr__(self, name: str, value: Any) -> None:
        # Invalidate cache when dependencies change
        if hasattr(self, "_cache") and name in self.__class__.model_fields:
            # Clear cache for properties that depend on this field
            for prop_name, deps in getattr(self, "_cache_dependencies", {}).items():
                if name in deps:
                    self._cache.pop(prop_name, None)

        super().__setattr__(name, value)
