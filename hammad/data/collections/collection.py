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
    from .base_collection import BaseCollection
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


class Collection:
    """
    A unified collection factory that creates the appropriate collection type
    based on the provided parameters.

    This class acts as a factory and doesn't contain its own logic - it simply
    returns instances of SearchableCollection or VectorCollection based on the
    type parameter.
    """

    @overload
    def __new__(
        cls,
        type: Literal["searchable"],
        name: str,
        *,
        schema: Optional[Any] = None,
        default_ttl: Optional[int] = None,
        storage_backend: Optional[Any] = None,
        heap_size: Optional[int] = None,
        num_threads: Optional[int] = None,
        index_path: Optional[str] = None,
        schema_builder: Optional[Any] = None,
        writer_memory: Optional[int] = None,
        reload_policy: Optional[str] = None,
    ) -> "SearchableCollection": ...

    @overload
    def __new__(
        cls,
        type: Literal["vector"],
        name: str,
        vector_size: int,
        *,
        schema: Optional[Any] = None,
        default_ttl: Optional[int] = None,
        storage_backend: Optional[Any] = None,
        distance_metric: Optional[Any] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
        model: Optional[str] = None,
        # Common embedding parameters
        format: bool = False,
        # LiteLLM parameters
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout: Optional[int] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        caching: bool = False,
        user: Optional[str] = None,
        # FastEmbed parameters
        parallel: Optional[int] = None,
        batch_size: Optional[int] = None,
        # Qdrant parameters
        path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        prefer_grpc: Optional[bool] = None,
        qdrant_timeout: Optional[float] = None,
    ) -> "VectorCollection": ...

    def __new__(
        cls,
        type: Literal["searchable", "vector"],
        name: str,
        vector_size: Optional[int] = None,
        *,
        schema: Optional[Any] = None,
        default_ttl: Optional[int] = None,
        storage_backend: Optional[Any] = None,
        distance_metric: Optional[Any] = None,
        embedding_function: Optional[Callable[[Any], List[float]]] = None,
        model: Optional[str] = None,
        # Common embedding parameters
        format: bool = False,
        # LiteLLM parameters
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout: Optional[int] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        caching: bool = False,
        user: Optional[str] = None,
        # FastEmbed parameters
        parallel: Optional[int] = None,
        batch_size: Optional[int] = None,
        # Tantivy parameters (searchable collections only)
        heap_size: Optional[int] = None,
        num_threads: Optional[int] = None,
        index_path: Optional[str] = None,
        schema_builder: Optional[Any] = None,
        writer_memory: Optional[int] = None,
        reload_policy: Optional[str] = None,
        # Qdrant parameters (vector collections only)
        path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        prefer_grpc: Optional[bool] = None,
        qdrant_timeout: Optional[float] = None,
    ) -> "BaseCollection":
        """
        Create a collection of the specified type.

        Args:
            type: Type of collection to create ("searchable" or "vector")
            name: Name of the collection
            vector_size: Size of vectors (required for vector collections)
            schema: Optional schema for type validation
            default_ttl: Default TTL for items in seconds
            storage_backend: Optional storage backend
            distance_metric: Distance metric for similarity search (vector collections only)
            embedding_function: Function to convert objects to vectors (vector collections only)

            Tantivy parameters (searchable collections only):
            heap_size: Memory allocation for tantivy heap
            num_threads: Number of threads for tantivy operations
            index_path: Path to store tantivy index files
            schema_builder: Custom schema builder for tantivy
            writer_memory: Memory allocation for tantivy writer
            reload_policy: Policy for reloading tantivy index

            Qdrant parameters (vector collections only):
            path: Path for local Qdrant storage
            host: Qdrant server host
            port: Qdrant server port
            grpc_port: Qdrant gRPC port
            prefer_grpc: Whether to prefer gRPC over HTTP
            api_key: API key for Qdrant authentication
            timeout: Request timeout for Qdrant operations

        Returns:
            A SearchableCollection or VectorCollection instance
        """
        if type == "searchable":
            from .searchable_collection import SearchableCollection

            # Build tantivy config from individual parameters
            tantivy_config = {}
            if heap_size is not None:
                tantivy_config["heap_size"] = heap_size
            if num_threads is not None:
                tantivy_config["num_threads"] = num_threads
            if index_path is not None:
                tantivy_config["index_path"] = index_path
            if schema_builder is not None:
                tantivy_config["schema_builder"] = schema_builder
            if writer_memory is not None:
                tantivy_config["writer_memory"] = writer_memory
            if reload_policy is not None:
                tantivy_config["reload_policy"] = reload_policy

            return SearchableCollection(
                name=name,
                schema=schema,
                default_ttl=default_ttl,
                storage_backend=storage_backend,
                tantivy_config=tantivy_config if tantivy_config else None,
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

            # Build qdrant config from individual parameters
            qdrant_config = {}
            if path is not None:
                qdrant_config["path"] = path
            if host is not None:
                qdrant_config["host"] = host
            if port is not None:
                qdrant_config["port"] = port
            if grpc_port is not None:
                qdrant_config["grpc_port"] = grpc_port
            if prefer_grpc is not None:
                qdrant_config["prefer_grpc"] = prefer_grpc
            if qdrant_timeout is not None:
                qdrant_config["timeout"] = qdrant_timeout

            return VectorCollection(
                name=name,
                vector_size=vector_size,
                schema=schema,
                default_ttl=default_ttl,
                storage_backend=storage_backend,
                distance_metric=distance_metric,
                qdrant_config=qdrant_config if qdrant_config else None,
                embedding_function=embedding_function,
                model=model,
                # Common embedding parameters
                format=format,
                # LiteLLM parameters
                dimensions=dimensions,
                encoding_format=encoding_format,
                timeout=timeout,
                api_base=api_base,
                api_version=api_version,
                api_key=api_key,
                api_type=api_type,
                caching=caching,
                user=user,
                # FastEmbed parameters
                parallel=parallel,
                batch_size=batch_size,
            )
        else:
            raise ValueError(f"Unsupported collection type: {type}")


@overload
def create_collection(
    type: Literal["searchable"],
    name: str,
    *,
    schema: Optional[Any] = None,
    default_ttl: Optional[int] = None,
    storage_backend: Optional[Any] = None,
    heap_size: Optional[int] = None,
    num_threads: Optional[int] = None,
    index_path: Optional[str] = None,
    schema_builder: Optional[Any] = None,
    writer_memory: Optional[int] = None,
    reload_policy: Optional[str] = None,
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
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
    model: Optional[str] = None,
    # Common embedding parameters
    format: bool = False,
    # LiteLLM parameters
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: Optional[int] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    api_type: Optional[str] = None,
    caching: bool = False,
    user: Optional[str] = None,
    # FastEmbed parameters
    parallel: Optional[int] = None,
    batch_size: Optional[int] = None,
    # Qdrant parameters
    path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    grpc_port: Optional[int] = None,
    prefer_grpc: Optional[bool] = None,
    qdrant_timeout: Optional[float] = None,
) -> "VectorCollection": ...


def create_collection(
    type: Literal["searchable", "vector"],
    name: str,
    vector_size: Optional[int] = None,
    *,
    schema: Optional[Any] = None,
    default_ttl: Optional[int] = None,
    storage_backend: Optional[Any] = None,
    distance_metric: Optional[Any] = None,
    embedding_function: Optional[Callable[[Any], List[float]]] = None,
    model: Optional[str] = None,
    # Common embedding parameters
    format: bool = False,
    # LiteLLM parameters
    dimensions: Optional[int] = None,
    encoding_format: Optional[str] = None,
    timeout: Optional[int] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    api_type: Optional[str] = None,
    caching: bool = False,
    user: Optional[str] = None,
    # FastEmbed parameters
    parallel: Optional[int] = None,
    batch_size: Optional[int] = None,
    # Tantivy parameters (searchable collections only)
    heap_size: Optional[int] = None,
    num_threads: Optional[int] = None,
    index_path: Optional[str] = None,
    schema_builder: Optional[Any] = None,
    writer_memory: Optional[int] = None,
    reload_policy: Optional[str] = None,
    # Qdrant parameters (vector collections only)
    path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    grpc_port: Optional[int] = None,
    prefer_grpc: Optional[bool] = None,
    qdrant_timeout: Optional[float] = None,
) -> "BaseCollection":
    """
    Create a collection of the specified type.

    This function provides a factory pattern for creating collections.
    Use the Collection class for a more object-oriented approach.

    Args:
        type: Type of collection to create ("searchable" or "vector")
        name: Name of the collection
        vector_size: Size of vectors (required for vector collections)
        schema: Optional schema for type validation
        default_ttl: Default TTL for items in seconds
        storage_backend: Optional storage backend
        distance_metric: Distance metric for similarity search (vector collections only)
        embedding_function: Function to convert objects to vectors (vector collections only)

        Tantivy parameters (searchable collections only):
        heap_size: Memory allocation for tantivy heap
        num_threads: Number of threads for tantivy operations
        index_path: Path to store tantivy index files
        schema_builder: Custom schema builder for tantivy
        writer_memory: Memory allocation for tantivy writer
        reload_policy: Policy for reloading tantivy index

        Qdrant parameters (vector collections only):
        path: Path for local Qdrant storage
        host: Qdrant server host
        port: Qdrant server port
        grpc_port: Qdrant gRPC port
        prefer_grpc: Whether to prefer gRPC over HTTP
        api_key: API key for Qdrant authentication
        timeout: Request timeout for Qdrant operations

    Returns:
        A SearchableCollection or VectorCollection instance
    """
    return Collection(
        type=type,
        name=name,
        vector_size=vector_size,
        schema=schema,
        default_ttl=default_ttl,
        storage_backend=storage_backend,
        distance_metric=distance_metric,
        embedding_function=embedding_function,
        model=model,
        format=format,
        dimensions=dimensions,
        encoding_format=encoding_format,
        timeout=timeout,
        api_base=api_base,
        api_version=api_version,
        api_key=api_key,
        api_type=api_type,
        caching=caching,
        user=user,
        parallel=parallel,
        batch_size=batch_size,
        heap_size=heap_size,
        num_threads=num_threads,
        index_path=index_path,
        schema_builder=schema_builder,
        writer_memory=writer_memory,
        reload_policy=reload_policy,
        path=path,
        host=host,
        port=port,
        grpc_port=grpc_port,
        prefer_grpc=prefer_grpc,
        qdrant_timeout=qdrant_timeout,
    )
