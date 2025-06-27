"""hammad.data.collections.collection"""

from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    overload,
    Any,
    List,
    Callable,
    Union,
)
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from .searchable_collection import SearchableCollection
    from .vector_collection import VectorCollection


Distance = Literal[
    "cosine",
    "euclidean",
    "manhattan",
    "hamming",
    "dot",
    "l2",
    "l1",
    "l2_squared",
    "l1_squared",
    "cosine_sim",
    "euclidean_sim",
    "manhattan_sim",
    "hamming_sim",
    "dot_sim",
]


class SearchableCollectionSettings(TypedDict, total=False):
    """Configuration settings for SearchableCollection using tantivy."""

    heap_size: int
    num_threads: Optional[int]
    index_path: Optional[str]
    schema_builder: Optional[Any]
    writer_memory: Optional[int]
    reload_policy: Optional[str]


class VectorCollectionSettings(TypedDict, total=False):
    """Configuration settings for VectorCollection using Qdrant."""

    path: Optional[str]
    host: Optional[str]
    port: Optional[int]
    grpc_port: Optional[int]
    prefer_grpc: Optional[bool]
    api_key: Optional[str]
    timeout: Optional[float]


@overload
def create_collection(
    type: Literal["searchable"],
    name: str,
    *,
    schema: Optional[Any] = None,
    default_ttl: Optional[int] = None,
    storage_backend: Optional[Any] = None,
    tantivy_settings: Optional[SearchableCollectionSettings] = None,
) -> "SearchableCollection": ...


@overload
def create_collection(
    type: Literal["vector"],
    name: str,
    vector_size: int,
    *,
    schema: Optional[Any] = None,
    default_ttl: Optional[int] = None,
    storage_backend: Optional[Any] = None,
    distance_metric: Optional[Any] = None,
    qdrant_settings: Optional[VectorCollectionSettings] = None,
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
) -> "VectorCollection": ...


def create_collection(
    type: Literal["searchable", "vector"],
    name: str,
    vector_size: Optional[int] = None,
    *,
    schema: Optional[Any] = None,
    default_ttl: Optional[int] = None,
    storage_backend: Optional[Any] = None,
    tantivy_settings: Optional[SearchableCollectionSettings] = None,
    distance_metric: Optional[Any] = None,
    qdrant_settings: Optional[VectorCollectionSettings] = None,
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
) -> Union["SearchableCollection", "VectorCollection"]:
    """
    Create a collection of the specified type.

    Args:
        type: Type of collection to create ("searchable" or "vector")
        name: Name of the collection
        vector_size: Size of vectors (required for vector collections)
        schema: Optional schema for type validation
        default_ttl: Default TTL for items in seconds
        storage_backend: Optional storage backend
        tantivy_settings: Configuration for tantivy search (searchable collections only)
        distance_metric: Distance metric for similarity search (vector collections only)
        qdrant_settings: Configuration for Qdrant (vector collections only)
        embedding_function: Function to convert objects to vectors (vector collections only)

    Returns:
        A SearchableCollection or VectorCollection instance
    """
    if type == "searchable":
        from .searchable_collection import SearchableCollection

        return SearchableCollection(
            name=name,
            schema=schema,
            default_ttl=default_ttl,
            storage_backend=storage_backend,
            tantivy_config=tantivy_settings,
        )
    elif type == "vector":
        if vector_size is None:
            raise ValueError("vector_size is required for vector collections")

        try:
            from .vector_collection import VectorCollection, Distance
        except ImportError:
            raise ImportError(
                "qdrant-client is required for vector collections. "
                "Please install it with 'pip install qdrant-client'."
            )

        # Set default distance metric if not provided and Distance is available
        if distance_metric is None and Distance is not None:
            distance_metric = Distance.DOT

        return VectorCollection(
            name=name,
            vector_size=vector_size,
            schema=schema,
            default_ttl=default_ttl,
            storage_backend=storage_backend,
            distance_metric=distance_metric,
            qdrant_config=qdrant_settings,
            embedding_function=embedding_function,
        )
    else:
        raise ValueError(f"Unsupported collection type: {type}")
