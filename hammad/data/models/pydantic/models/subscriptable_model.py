"""hammad.data.models.pydantic.models.subscriptable_model"""

from pydantic import BaseModel
from typing import Any

__all__ = ("SubscriptableModel",)


class SubscriptableModel(BaseModel):
    """
    A pydantic model that allows for dict-like access to its fields.
    """

    def __getitem__(self, key: str) -> Any:
        """Get field value using dict-like access.

        Usage:
            >>> msg = Message(role='user')
            >>> msg['role']
            'user'
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set field value using dict-like access.

        Usage:
            >>> msg = Message(role='user')
            >>> msg['role'] = 'assistant'
            >>> msg['role']
            'assistant'
        """
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        """Check if field exists using 'in' operator.

        Usage:
            >>> msg = Message(role='user')
            >>> 'role' in msg
            True
            >>> 'nonexistent' in msg
            False
        """
        if hasattr(self, key):
            return True
        if value := self.__class__.model_fields.get(key):
            return value.default is not None
        return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get field value with optional default.

        Usage:
            >>> msg = Message(role='user')
            >>> msg.get('role')
            'user'
            >>> msg.get('nonexistent', 'default')
            'default'
        """
        return getattr(self, key) if hasattr(self, key) else default
