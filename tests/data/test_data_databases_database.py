import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from hammad.data.databases.database import Database


def test_database_init():
    """Test database initialization."""
    db = Database()
    assert db.location == "memory"
    assert db.path == "database.db"
    assert db.default_ttl is None
    assert len(db.keys()) == 0

    db_with_ttl = Database(location="memory", default_ttl=3600)
    assert db_with_ttl.location == "memory"
    assert db_with_ttl.default_ttl == 3600

    # Test file location with custom path
    db_file = Database(location="file", path="custom.db")
    assert db_file.location == "file"
    assert db_file.path == "custom.db"


def test_database_repr():
    """Test database string representation."""
    db = Database()
    repr_str = repr(db)
    assert "Database" in repr_str
    assert "memory" in repr_str
    assert "collections=" in repr_str

    # Test file database repr
    db_file = Database(location="file", path="test.db")
    repr_str = repr(db_file)
    assert "Database" in repr_str
    assert "file" in repr_str
    assert "test.db" in repr_str
    assert "collections=" in repr_str


def test_traditional_collection_operations():
    """Test traditional collection CRUD operations."""
    db = Database()

    # Add items to default collection
    db.add("test_value", id="test_id")
    assert db.get("test_id") == "test_value"

    # Add to named collection
    db.add("collection_value", id="coll_id", collection="test_collection")
    assert db.get("coll_id", collection="test_collection") == "collection_value"

    # Test collection exists
    assert "default" in db
    assert "test_collection" in db


def test_collection_accessor():
    """Test collection accessor functionality."""
    db = Database()

    # Get collection accessor
    collection = db["test_collection"]

    # Add through accessor
    collection.add("test_data", id="test_id")

    # Get through accessor
    result = collection.get("test_id")
    assert result == "test_data"

    # Query through accessor
    results = collection.query()
    assert "test_data" in results


def test_filters():
    """Test filtering functionality."""
    db = Database()

    # Add items with filters
    db.add("item1", id="id1", filters={"category": "A", "priority": 1})
    db.add("item2", id="id2", filters={"category": "B", "priority": 2})
    db.add("item3", id="id3", filters={"category": "A", "priority": 2})

    # Query with filters
    results = db.query(filters={"category": "A"})
    assert len(results) == 2
    assert "item1" in results
    assert "item3" in results

    # More specific filter
    results = db.query(filters={"category": "A", "priority": 1})
    assert len(results) == 1
    assert "item1" in results


def test_search():
    """Test basic search functionality."""
    db = Database()

    db.add("apple pie recipe", id="id1")
    db.add("banana bread recipe", id="id2")
    db.add("chocolate cake", id="id3")

    # Search for recipes
    results = db.query(search="recipe")
    assert len(results) == 2
    assert "apple pie recipe" in results
    assert "banana bread recipe" in results

    # Case insensitive search
    results = db.query(search="APPLE")
    assert len(results) == 1
    assert "apple pie recipe" in results


def test_limit():
    """Test query limit functionality."""
    db = Database()

    for i in range(10):
        db.add(f"item_{i}", id=f"id_{i}")

    # Test limit
    results = db.query(limit=5)
    assert len(results) == 5

    # Test with no limit
    results = db.query()
    assert len(results) == 10


def test_ttl():
    """Test TTL functionality."""
    import time

    db = Database(default_ttl=1)  # 1 second TTL

    # Add item with short TTL
    db.add("expires_soon", id="ttl_test", ttl=1)

    # Should exist immediately
    assert db.get("ttl_test") == "expires_soon"

    # Wait for expiration (in real tests you might mock time)
    time.sleep(1.1)

    # Should be expired and return None
    # Note: Expiration is checked on access
    assert db.get("ttl_test") is None


def test_create_searchable_collection():
    """Test creating searchable collections."""
    db = Database()

    # Create searchable collection
    collection = db.create_searchable_collection("search_test")
    assert "search_test" in db.collections()
    assert collection.name == "search_test"

    # Collection should be accessible
    assert "search_test" in db
    retrieved = db["search_test"]
    assert retrieved.name == "search_test"


def test_create_vector_collection():
    """Test creating vector collections."""
    db = Database()

    # Create vector collection
    collection = db.create_vector_collection("vector_test", vector_size=128)
    assert "vector_test" in db.collections()
    assert collection.name == "vector_test"
    assert collection.vector_size == 128

    # Collection should be accessible
    assert "vector_test" in db
    retrieved = db["vector_test"]
    assert retrieved.name == "vector_test"


def test_create_vector_collection_with_embedding_parameters():
    """Test creating vector collections with embedding parameters."""
    db = Database()

    # Create vector collection with FastEmbed parameters
    collection = db.create_vector_collection(
        "fastembed_test",
        vector_size=384,
        model="fastembed/BAAI/bge-small-en-v1.5",
        format=True,
        parallel=4,
        batch_size=32,
    )
    assert collection.name == "fastembed_test"
    assert collection.vector_size == 384
    assert collection._model == "fastembed/BAAI/bge-small-en-v1.5"
    assert collection._embedding_params["format"] is True
    assert collection._embedding_params["parallel"] == 4
    assert collection._embedding_params["batch_size"] == 32

    # Create vector collection with LiteLLM parameters
    collection2 = db.create_vector_collection(
        "litellm_test",
        vector_size=1536,
        model="text-embedding-ada-002",
        dimensions=1536,
        api_key="sk-test",
        timeout=600,
        caching=True,
    )
    assert collection2.name == "litellm_test"
    assert collection2.vector_size == 1536
    assert collection2._model == "text-embedding-ada-002"
    assert collection2._embedding_params["dimensions"] == 1536
    assert collection2._embedding_params["api_key"] == "sk-test"
    assert collection2._embedding_params["timeout"] == 600
    assert collection2._embedding_params["caching"] is True


def test_create_vector_collection_with_qdrant_parameters():
    """Test creating vector collections with Qdrant configuration parameters."""
    db = Database()

    # Create vector collection with Qdrant parameters
    collection = db.create_vector_collection(
        "qdrant_test",
        vector_size=256,
        path="/tmp/test_qdrant",
        host="localhost",
        port=6333,
        grpc_port=6334,
        prefer_grpc=True,
        qdrant_timeout=30.0,
    )

    assert collection.name == "qdrant_test"
    assert collection.vector_size == 256
    # Note: Qdrant config is internal to the collection
    # We're mainly testing that the parameters are accepted


def test_register_collection():
    """Test registering external collections."""
    from hammad.data.collections.collection import create_collection

    db = Database()

    # Create external collection
    external_collection = create_collection("searchable", "external_test")

    # Register with database
    db.register_collection(external_collection)

    assert "external_test" in db.collections()
    assert db["external_test"] == external_collection


def test_delete_collection():
    """Test deleting collections."""
    db = Database()

    # Create traditional collection
    db.create_collection("traditional")
    assert "traditional" in db

    # Create modern collection
    db.create_searchable_collection("modern")
    assert "modern" in db

    # Delete traditional collection
    result = db.delete_collection("traditional")
    assert result is True
    assert "traditional" not in db

    # Delete modern collection
    result = db.delete_collection("modern")
    assert result is True
    assert "modern" not in db

    # Delete non-existent collection
    result = db.delete_collection("nonexistent")
    assert result is False


def test_clear():
    """Test clearing all data."""
    db = Database()

    # Add some data
    db.add("test", id="test_id")
    db.create_searchable_collection("test_collection")

    assert len(db.keys()) > 0

    # Clear everything
    db.clear()

    assert len(db.keys()) == 0
    assert len(db.collections()) == 0


def test_keys():
    """Test getting all collection names."""
    db = Database()

    # Initially empty (except default gets created on first use)
    initial_keys = db.keys()

    # Add traditional collection
    db.create_collection("traditional")

    # Add modern collection
    db.create_searchable_collection("modern")

    keys = db.keys()
    assert "traditional" in keys
    assert "modern" in keys
    assert len(keys) >= 2


def test_collections():
    """Test getting modern collections."""
    db = Database()

    # Create some collections
    coll1 = db.create_searchable_collection("search1")
    coll2 = db.create_vector_collection("vector1", vector_size=64)

    collections = db.collections()
    assert len(collections) == 2
    assert collections["search1"] == coll1
    assert collections["vector1"] == coll2


def test_mixed_collection_types():
    """Test using both traditional and modern collections."""
    db = Database()

    # Traditional collection
    db.add("traditional_item", id="trad_id", collection="traditional")

    # Modern searchable collection
    search_coll = db.create_searchable_collection("searchable")
    search_coll.add("searchable_item", id="search_id")

    # Modern vector collection
    vector_coll = db.create_vector_collection("vector", vector_size=3)
    vector_coll.add([1.0, 0.0, 0.0], "vector_id")

    # All should be accessible
    assert db.get("trad_id", collection="traditional") == "traditional_item"
    assert db["searchable"].get("search_id") == "searchable_item"
    assert db["vector"].get("vector_id") == [1.0, 0.0, 0.0]

    # All should show up in keys
    keys = db.keys()
    assert "traditional" in keys
    assert "searchable" in keys
    assert "vector" in keys


def test_database_as_storage_backend():
    """Test database acting as storage backend for collections."""
    from hammad.data.collections.collection import create_collection

    db = Database()

    # Create collection with database as backend
    collection = create_collection("searchable", "backend_test", storage_backend=db)

    # Add data through collection
    collection.add("test_data", "test_id")

    # Should be accessible through database
    assert db.get("test_id", collection="backend_test") == "test_data"


def test_file_storage_basic_operations():
    """Test basic CRUD operations with file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        # Add items
        db.add("test_value", id="test_id")
        assert db.get("test_id") == "test_value"

        # Add to named collection
        db.add("collection_value", id="coll_id", collection="test_collection")
        assert db.get("coll_id", collection="test_collection") == "collection_value"

        # Test persistence by creating new database instance
        db2 = Database(location="file", path=db_path)
        assert db2.get("test_id") == "test_value"
        assert db2.get("coll_id", collection="test_collection") == "collection_value"


def test_file_storage_with_filters():
    """Test file storage with filtering functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        # Add items with filters
        db.add("item1", id="id1", filters={"category": "A", "priority": 1})
        db.add("item2", id="id2", filters={"category": "B", "priority": 2})
        db.add("item3", id="id3", filters={"category": "A", "priority": 2})

        # Query with filters
        results = db.query(filters={"category": "A"})
        assert len(results) == 2
        assert "item1" in results
        assert "item3" in results

        # Test persistence of filters
        db2 = Database(location="file", path=db_path)
        results = db2.query(filters={"category": "A", "priority": 1})
        assert len(results) == 1
        assert "item1" in results


def test_file_storage_search():
    """Test file storage search functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        db.add("apple pie recipe", id="id1")
        db.add("banana bread recipe", id="id2")
        db.add("chocolate cake", id="id3")

        # Search for recipes
        results = db.query(search="recipe")
        assert len(results) == 2
        assert "apple pie recipe" in results
        assert "banana bread recipe" in results

        # Test persistence of search
        db2 = Database(location="file", path=db_path)
        results = db2.query(search="APPLE")
        assert len(results) == 1
        assert "apple pie recipe" in results


def test_file_storage_ttl():
    """Test TTL functionality with file storage."""
    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path, default_ttl=1)

        # Add item with short TTL
        db.add("expires_soon", id="ttl_test", ttl=1)

        # Should exist immediately
        assert db.get("ttl_test") == "expires_soon"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired and return None
        assert db.get("ttl_test") is None

        # Test that expired items are cleaned up from file storage
        db2 = Database(location="file", path=db_path)
        assert db2.get("ttl_test") is None


def test_file_storage_searchable_collections():
    """Test searchable collections with file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        # Create searchable collection
        collection = db.create_searchable_collection("search_test")
        assert collection.name == "search_test"

        # Add data
        collection.add("searchable content", "search_id")

        # Test retrieval
        result = collection.get("search_id")
        assert result == "searchable content"


def test_file_storage_mixed_collections():
    """Test mixed collection types with file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        # Traditional collection
        db.add("traditional_item", id="trad_id", collection="traditional")

        # Modern searchable collection
        search_coll = db.create_searchable_collection("searchable")
        search_coll.add("searchable_item", "search_id")

        # Test persistence of all collection types
        db2 = Database(location="file", path=db_path)
        assert db2.get("trad_id", collection="traditional") == "traditional_item"
        assert db2["searchable"].get("search_id") == "searchable_item"

        # All should show up in keys
        keys = db2.keys()
        assert "traditional" in keys
        assert "searchable" in keys


def test_file_storage_directory_creation():
    """Test that database creates necessary directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = os.path.join(temp_dir, "nested", "dirs", "test.db")

        # Directory doesn't exist yet
        assert not os.path.exists(os.path.dirname(nested_path))

        # Creating database should create the directory
        db = Database(location="file", path=nested_path)
        db.add("test", id="test_id")

        # Directory should now exist
        assert os.path.exists(os.path.dirname(nested_path))
        assert os.path.exists(nested_path)


def test_file_storage_update_operations():
    """Test update operations with file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)

        # Add initial item
        db.add("original_value", id="update_test")
        assert db.get("update_test") == "original_value"

        # Update the item (same ID, new value)
        db.add("updated_value", id="update_test")
        assert db.get("update_test") == "updated_value"

        # Test persistence of update
        db2 = Database(location="file", path=db_path)
        assert db2.get("update_test") == "updated_value"


@pytest.mark.skipif(
    not os.environ.get("TEST_SQLALCHEMY"),
    reason="SQLAlchemy not available or not testing file storage",
)
def test_file_storage_requires_sqlalchemy():
    """Test that file storage requires SQLAlchemy."""
    # This test would need to be run in an environment without SQLAlchemy
    # to test the ImportError handling
    pass


@patch("hammad.ai.embeddings.create.create_embeddings")
def test_database_vector_collection_with_embedding_model(mock_create_embeddings):
    """Test database vector collection integration with embedding models."""
    # Mock the embedding response
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
    mock_create_embeddings.return_value = mock_response

    db = Database()

    # Create vector collection with embedding model
    collection = db.create_vector_collection(
        "ai_docs",
        vector_size=3,
        model="text-embedding-ada-002",
        dimensions=3,
        api_key="test-key",
        timeout=600,
    )

    # Add document that should be embedded
    returned_id = collection.add("Machine learning fundamentals", "doc1")
    assert returned_id == "doc1"

    # Verify embedding was called with correct parameters
    mock_create_embeddings.assert_called_once()
    call_kwargs = mock_create_embeddings.call_args.kwargs
    assert call_kwargs["model"] == "text-embedding-ada-002"
    assert call_kwargs["input"] == "Machine learning fundamentals"
    assert call_kwargs["dimensions"] == 3
    assert call_kwargs["api_key"] == "test-key"
    assert call_kwargs["timeout"] == 600

    # Verify document can be retrieved
    result = collection.get("doc1")
    assert result == "Machine learning fundamentals"

    # Test semantic search
    mock_create_embeddings.reset_mock()
    results = collection.query("AI fundamentals", limit=1)

    # Verify search embedding was called
    mock_create_embeddings.assert_called_once()
    search_kwargs = mock_create_embeddings.call_args.kwargs
    assert search_kwargs["input"] == "AI fundamentals"

    # Verify results structure
    assert isinstance(results, list)


def test_database_mixed_embedding_models():
    """Test database with multiple vector collections using different embedding models."""
    db = Database()

    # Create FastEmbed collection
    fastembed_coll = db.create_vector_collection(
        "fastembed_docs",
        vector_size=384,
        model="fastembed/BAAI/bge-small-en-v1.5",
        parallel=2,
        batch_size=16,
        format=True,
    )

    # Create LiteLLM collection
    litellm_coll = db.create_vector_collection(
        "openai_docs",
        vector_size=1536,
        model="text-embedding-ada-002",
        dimensions=1536,
        api_key="sk-test",
        caching=True,
    )

    # Verify both collections exist and have correct configurations
    assert "fastembed_docs" in db.collections()
    assert "openai_docs" in db.collections()

    assert fastembed_coll.vector_size == 384
    assert litellm_coll.vector_size == 1536

    assert fastembed_coll._model == "fastembed/BAAI/bge-small-en-v1.5"
    assert litellm_coll._model == "text-embedding-ada-002"

    assert fastembed_coll._embedding_params["parallel"] == 2
    assert litellm_coll._embedding_params["dimensions"] == 1536


def test_database_vector_collection_parameter_combinations():
    """Test various parameter combinations for vector collections."""
    db = Database()

    # Test with minimal parameters
    minimal_coll = db.create_vector_collection("minimal", vector_size=128)
    assert minimal_coll.name == "minimal"
    assert minimal_coll.vector_size == 128
    assert minimal_coll._model is None

    # Test with embedding function but no model
    def simple_embedding(text):
        return [float(ord(c)) for c in text[:128].ljust(128, "a")]

    func_coll = db.create_vector_collection(
        "with_function", vector_size=128, embedding_function=simple_embedding
    )
    assert func_coll._embedding_function is not None
    assert func_coll._model is None

    # Test with all FastEmbed parameters
    full_fastembed = db.create_vector_collection(
        "full_fastembed",
        vector_size=384,
        model="fastembed/BAAI/bge-small-en-v1.5",
        format=True,
        parallel=4,
        batch_size=64,
        # Qdrant parameters
        path="/tmp/test_qdrant",
        prefer_grpc=False,
    )
    assert full_fastembed._model == "fastembed/BAAI/bge-small-en-v1.5"
    assert full_fastembed._embedding_params["format"] is True
    assert full_fastembed._embedding_params["parallel"] == 4
    assert full_fastembed._embedding_params["batch_size"] == 64

    # Test with all LiteLLM parameters
    full_litellm = db.create_vector_collection(
        "full_litellm",
        vector_size=1536,
        model="text-embedding-3-large",
        format=True,
        dimensions=1536,
        encoding_format="float",
        timeout=900,
        api_base="https://api.openai.com/v1",
        api_version="2023-05-15",
        api_key="sk-test",
        api_type="openai",
        caching=True,
        user="test-user",
        # Qdrant parameters
        host="localhost",
        port=6333,
        grpc_port=6334,
        prefer_grpc=True,
        qdrant_timeout=60.0,
    )
    assert full_litellm._model == "text-embedding-3-large"
    assert full_litellm._embedding_params["dimensions"] == 1536
    assert full_litellm._embedding_params["encoding_format"] == "float"
    assert full_litellm._embedding_params["timeout"] == 900
    assert full_litellm._embedding_params["api_base"] == "https://api.openai.com/v1"
    assert full_litellm._embedding_params["api_version"] == "2023-05-15"
    assert full_litellm._embedding_params["api_key"] == "sk-test"
    assert full_litellm._embedding_params["api_type"] == "openai"
    assert full_litellm._embedding_params["caching"] is True
    assert full_litellm._embedding_params["user"] == "test-user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
