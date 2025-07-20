"""hammad.data.collections.indexes.tantivy.settings"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
)

__all__ = ("TantivyCollectionIndexSettings", "TantivyCollectionIndexQuerySettings")


@dataclass
class TantivyCollectionIndexSettings:
    """Object representation of user configurable settings
    that can be used to configure a `TantivyCollectionIndex`."""

    fast: bool = True
    """Whether to use fast schema building & indexing from
    `tantivy`'s builtin implementation."""

    def get_tantivy_config(self) -> Dict[str, Any]:
        """Returns a configuration dictionary used
        to configure the tantivy index internally."""

        return {
            "text_fields": {"stored": True, "fast": self.fast},
            "numeric_fields": {"stored": True, "indexed": True, "fast": self.fast},
            "date_fields": {"stored": True, "indexed": True, "fast": self.fast},
            "json_fields": {"stored": True},
        }


@dataclass
class TantivyCollectionIndexQuerySettings:
    """Object representation of user configurable settings
    that can be used to configure the query engine for a
    `TantivyCollectionIndex`."""

    limit: int = 10
    """The maximum number of results to return."""
