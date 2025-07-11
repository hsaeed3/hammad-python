"""hammad.data.collections.indexes.qdrant.settings"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Optional,
    Literal,
)

__all__ = (
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
    "DistanceMetric",
)


DistanceMetric = Literal[
    "cosine",
    "dot",
    "euclidean",
    "manhattan",
]


@dataclass
class QdrantCollectionIndexSettings:
    """Object representation of user configurable settings
    that can be used to configure a `QdrantCollectionIndex`."""

    vector_size: int = 768
    """The size/dimension of the vectors to store."""

    distance_metric: DistanceMetric = "dot"
    """Distance metric for similarity search."""

    path: Optional[str] = None
    """Path for local Qdrant storage (None = in-memory)."""

    host: Optional[str] = None
    """Qdrant server host (if using remote server)."""

    port: int = 6333
    """Qdrant server port."""

    grpc_port: int = 6334
    """Qdrant gRPC port."""

    prefer_grpc: bool = False
    """Whether to prefer gRPC over HTTP."""

    api_key: Optional[str] = None
    """API key for Qdrant authentication."""

    timeout: Optional[float] = None
    """Request timeout for Qdrant operations."""

    def get_qdrant_config(self) -> Dict[str, Any]:
        """Returns a configuration dictionary used
        to configure the qdrant client internally."""
        config = {}

        if self.path is not None:
            config["path"] = self.path
        elif self.host is not None:
            config["host"] = self.host
            config["port"] = self.port
            config["grpc_port"] = self.grpc_port
            config["prefer_grpc"] = self.prefer_grpc
            if self.api_key:
                config["api_key"] = self.api_key
            if self.timeout:
                config["timeout"] = self.timeout
        else:
            # In-memory database
            config["location"] = ":memory:"

        return config


@dataclass
class QdrantCollectionIndexQuerySettings:
    """Object representation of user configurable settings
    that can be used to configure the query engine for a
    `QdrantCollectionIndex`."""

    limit: int = 10
    """The maximum number of results to return."""

    score_threshold: Optional[float] = None
    """Minimum similarity score threshold for results."""

    exact: bool = False
    """Whether to use exact search (slower but more accurate)."""
