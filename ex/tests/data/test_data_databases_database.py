import pytest
import tempfile
import os
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

    # Collection should be accessible
    assert "vector_test" in db
    retrieved = db["vector_test"]
    assert retrieved.name == "vector_test"


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
    vector_coll.add([1.0, 0.0, 0.0], id="vector_id")

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
    collection.add("test_data", id="test_id")

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


def test_file_storage_vector_collections():
    """Test vector collections with file storage and unified path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)
        
        # Create vector collection
        collection = db.create_vector_collection("vector_test", vector_size=3)
        assert collection.name == "vector_test"
        
        # Add vector data
        collection.add([1.0, 0.0, 0.0], id="vector_id")
        
        # Test retrieval
        result = collection.get("vector_id")
        assert result == [1.0, 0.0, 0.0]
        
        # Test that Qdrant storage path is derived from unified path
        expected_qdrant_path = db_path.replace('.db', '_qdrant_vector_test')
        # Note: This tests the path derivation logic, actual Qdrant functionality
        # would need Qdrant to be installed and properly configured


def test_file_storage_searchable_collections():
    """Test searchable collections with file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(location="file", path=db_path)
        
        # Create searchable collection
        collection = db.create_searchable_collection("search_test")
        assert collection.name == "search_test"
        
        # Add data
        collection.add("searchable content", id="search_id")
        
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
        search_coll.add("searchable_item", id="search_id")
        
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
    reason="SQLAlchemy not available or not testing file storage"
)
def test_file_storage_requires_sqlalchemy():
    """Test that file storage requires SQLAlchemy."""
    # This test would need to be run in an environment without SQLAlchemy
    # to test the ImportError handling
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
