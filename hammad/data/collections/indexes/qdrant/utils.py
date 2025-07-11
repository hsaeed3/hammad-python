"""hammad.data.collections.indexes.qdrant.utils"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, final
import uuid

from .....cache import cached
from .settings import (
    QdrantCollectionIndexSettings,
    QdrantCollectionIndexQuerySettings,
    DistanceMetric,
)

# Lazy imports to avoid errors when qdrant is not installed
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

__all__ = (
    "QdrantCollectionIndexError",
    "QdrantClientWrapper",
    "create_qdrant_client",
    "prepare_vector",
    "convert_distance_metric",
    "serialize",
)


class QdrantCollectionIndexError(Exception):
    """Exception raised when an error occurs in the `QdrantCollectionIndex`."""


@dataclass
class QdrantClientWrapper:
    """Wrapper over the qdrant client and collection setup."""

    client: Any
    """The qdrant client object."""

    collection_name: str
    """The name of the qdrant collection."""


@cached
def convert_distance_metric(metric: DistanceMetric) -> Any:
    """Convert string distance metric to qdrant Distance enum."""
    try:
        from qdrant_client.models import Distance

        mapping = {
            "cosine": Distance.COSINE,
            "dot": Distance.DOT,
            "euclidean": Distance.EUCLID,
            "manhattan": Distance.MANHATTAN,
        }

        return mapping.get(metric, Distance.DOT)
    except ImportError:
        raise QdrantCollectionIndexError(
            "qdrant-client is required for QdrantCollectionIndex. "
            "Install with: pip install qdrant-client"
        )


@cached
def create_qdrant_client(settings: QdrantCollectionIndexSettings) -> Any:
    """Create a qdrant client from settings."""
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        raise QdrantCollectionIndexError(
            "qdrant-client is required for QdrantCollectionIndex. "
            "Install with: pip install qdrant-client"
        )

    config = settings.get_qdrant_config()

    if "path" in config:
        # Local persistent storage
        return QdrantClient(path=config["path"])
    elif "host" in config:
        # Remote server
        client_kwargs = {
            "host": config["host"],
            "port": config.get("port", 6333),
            "grpc_port": config.get("grpc_port", 6334),
            "prefer_grpc": config.get("prefer_grpc", False),
        }

        if config.get("api_key"):
            client_kwargs["api_key"] = config["api_key"]
        if config.get("timeout"):
            client_kwargs["timeout"] = config["timeout"]

        return QdrantClient(**client_kwargs)
    else:
        # In-memory database
        return QdrantClient(":memory:")


def prepare_vector(
    vector: Union[List[float], Any],
    expected_size: int,
) -> List[float]:
    """Prepare and validate a vector for qdrant storage."""
    if NUMPY_AVAILABLE and hasattr(vector, "tolist"):
        # Handle numpy arrays
        vector = vector.tolist()
    elif not isinstance(vector, list):
        raise QdrantCollectionIndexError(
            f"Vector must be a list or numpy array, got {type(vector)}"
        )

    if len(vector) != expected_size:
        raise QdrantCollectionIndexError(
            f"Vector size {len(vector)} doesn't match expected size {expected_size}"
        )

    # Ensure all elements are floats
    try:
        return [float(x) for x in vector]
    except (TypeError, ValueError) as e:
        raise QdrantCollectionIndexError(f"Vector contains non-numeric values: {e}")


def build_qdrant_filter(filters: Optional[Dict[str, Any]]) -> Optional[Any]:
    """Build qdrant filter from filters dict."""
    if not filters:
        return None

    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        conditions = []
        for key, value in filters.items():
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        if len(conditions) == 1:
            return Filter(must=[conditions[0]])
        else:
            return Filter(must=conditions)

    except ImportError:
        raise QdrantCollectionIndexError(
            "qdrant-client is required for QdrantCollectionIndex. "
            "Install with: pip install qdrant-client"
        )


def create_collection_if_not_exists(
    client: Any,
    collection_name: str,
    settings: QdrantCollectionIndexSettings,
) -> None:
    """Create qdrant collection if it doesn't exist."""
    try:
        from qdrant_client.models import VectorParams

        # Check if collection exists
        try:
            collections = client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if collection_name not in collection_names:
                # Create collection
                distance_metric = convert_distance_metric(settings.distance_metric)

                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.vector_size, distance=distance_metric
                    ),
                )
        except Exception:
            # Collection might already exist or other issue
            pass

    except ImportError:
        raise QdrantCollectionIndexError(
            "qdrant-client is required for QdrantCollectionIndex. "
            "Install with: pip install qdrant-client"
        )


@cached
def serialize(obj: Any) -> Any:
    """Serialize an object to JSON-compatible format."""
    try:
        from msgspec import json

        return json.decode(json.encode(obj))
    except Exception:
        # Fallback to manual serialization if msgspec fails
        from dataclasses import is_dataclass, asdict

        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            return serialize(asdict(obj))
        elif hasattr(obj, "__dict__"):
            return serialize(obj.__dict__)
        else:
            return str(obj)
