import pytest
import tempfile
import time
import os
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from pydantic import BaseModel

from hammad.database import Database, DatabaseEntry


@pytest.fixture(autouse=True)
def cleanup_database_files():
    """Automatically cleanup database files created during tests."""
    yield
    # Cleanup after each test
    db_files = [
        "cursives_database.db",
        "cursives_database.db-journal",
        "cursives_database.db-wal",
        "cursives_database.db-shm",
    ]
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except (OSError, PermissionError):
                pass  # File might be in use, ignore


# Test data classes and models
@dataclass
class User:
    name: str
    email: str
    age: int = 25


class Product(BaseModel):
    name: str
    price: float
    category: str = "general"


class TestDatabaseBasics:
    """Test basic database functionality for both memory and disk storage."""

    def test_memory_database_initialization(self):
        """Test initializing a memory database."""
        db = Database(location="memory")
        assert db.location == "memory"
        assert db.default_ttl is None
        assert db.verbose is False
        assert db._engine is None
        assert "default" in db._storage

    def test_memory_database_with_options(self):
        """Test initializing memory database with options."""
        db = Database(location="memory", default_ttl=300, verbose=True)
        assert db.default_ttl == 300
        assert db.verbose is True

    def test_disk_database_initialization(self):
        """Test initializing a disk database."""
        db = Database(location="disk", verbose=False)
        assert db.location == "disk"
        assert db._engine is not None

    def test_basic_add_and_get_memory(self):
        """Test basic add and get operations in memory."""
        db = Database(location="memory")

        # Add item without ID
        db.add({"name": "John", "age": 30})

        # Add item with specific ID
        db.add({"name": "Jane", "age": 25}, id="user_1")

        # Get item by ID
        result = db.get("user_1")
        assert result == {"name": "Jane", "age": 25}

    def test_basic_add_and_get_disk(self):
        """Test basic add and get operations on disk."""
        db = Database(location="disk")

        # Add item with specific ID
        db.add({"name": "Alice", "role": "admin"}, id="admin_1")

        # Get item by ID
        result = db.get("admin_1")
        assert result == {"name": "Alice", "role": "admin"}

    def test_nonexistent_item(self):
        """Test getting non-existent items."""
        db = Database(location="memory")
        result = db.get("nonexistent")
        assert result is None

    def test_nonexistent_collection(self):
        """Test getting from non-existent collection."""
        db = Database(location="memory")
        result = db.get("any_id", collection="nonexistent")
        assert result is None


class TestCollections:
    """Test database collection functionality."""

    def test_create_collection_explicitly(self):
        """Test explicitly creating collections."""
        db = Database(location="memory")
        db.create_collection("users")
        assert "users" in db._schemas
        assert db._schemas["users"] is None

    def test_create_collection_with_schema(self):
        """Test creating collection with schema."""
        db = Database(location="memory")
        db.create_collection("products", schema=Product)
        assert db._schemas["products"] == Product

    def test_create_collection_with_ttl(self):
        """Test creating collection with custom TTL."""
        db = Database(location="memory")
        db.create_collection("sessions", default_ttl=3600)
        assert db._collection_ttls["sessions"] == 3600

    def test_multiple_collections(self):
        """Test working with multiple collections."""
        db = Database(location="memory")

        # Add to different collections
        db.add({"name": "John"}, id="user1", collection="users")
        db.add({"title": "Admin"}, id="role1", collection="roles")

        # Get from specific collections
        user = db.get("user1", collection="users")
        role = db.get("role1", collection="roles")

        assert user == {"name": "John"}
        assert role == {"title": "Admin"}

        # Should not find in wrong collection
        assert db.get("user1", collection="roles") is None

    def test_schema_consistency_enforcement(self):
        """Test that schema consistency is enforced."""
        db = Database(location="memory")
        db.create_collection("typed", schema=Product)

        # Should raise error when trying to create with different schema
        with pytest.raises(TypeError, match="already exists with a different schema"):
            db.create_collection("typed", schema=User)


class TestFilters:
    """Test filter functionality."""

    def test_add_with_filters(self):
        """Test adding items with filters."""
        db = Database(location="memory")

        db.add(
            {"name": "Alice"},
            id="user1",
            filters={"department": "engineering", "active": True},
        )

        # Should find with matching filters
        result = db.get("user1", filters={"department": "engineering"})
        assert result == {"name": "Alice"}

        # Should find with partial matching filters
        result = db.get("user1", filters={"active": True})
        assert result == {"name": "Alice"}

    def test_filter_mismatch(self):
        """Test that mismatched filters return None."""
        db = Database(location="memory")

        db.add(
            {"name": "Bob"}, id="user2", filters={"department": "sales", "active": True}
        )

        # Should not find with mismatched filters
        result = db.get("user2", filters={"department": "engineering"})
        assert result is None

        result = db.get("user2", filters={"active": False})
        assert result is None

    def test_no_filters_matches_any(self):
        """Test that no filters in query matches any item."""
        db = Database(location="memory")

        db.add({"name": "Charlie"}, id="user3", filters={"department": "hr"})

        # Should find without specifying filters
        result = db.get("user3")
        assert result == {"name": "Charlie"}

    def test_item_without_filters(self):
        """Test querying items that don't have filters."""
        db = Database(location="memory")

        db.add({"name": "Dave"}, id="user4")  # No filters

        # Should not match when filters are required
        result = db.get("user4", filters={"department": "any"})
        assert result is None

        # Should match when no filters specified
        result = db.get("user4")
        assert result == {"name": "Dave"}


class TestTTL:
    """Test TTL (Time To Live) functionality."""

    def test_ttl_item_level(self, monkeypatch):
        """Test TTL at item level."""
        db = Database(location="memory")

        # Add item with short TTL
        db.add({"temp": "data"}, id="temp1", ttl=1)

        # Should be available immediately
        result = db.get("temp1")
        assert result == {"temp": "data"}

        # Simulate expiration by directly modifying the stored expiration time
        # to be in the past
        past_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        item_data = db._storage["default"]["temp1"]
        item_data["expires_at"] = past_time

        # Should be expired now
        result = db.get("temp1")
        assert result is None

    def test_ttl_collection_level(self):
        """Test TTL at collection level."""
        db = Database(location="memory")

        # Create collection with TTL
        db.create_collection("temp_data", default_ttl=300)

        # Add item without specific TTL (should use collection default)
        db.add({"data": "value"}, id="item1", collection="temp_data")

        # Check that expires_at is set correctly
        item_data = db._storage["temp_data"]["item1"]
        assert item_data["expires_at"] is not None

    def test_ttl_database_level(self):
        """Test TTL at database level."""
        db = Database(location="memory", default_ttl=600)

        # Add item without specific TTL (should use database default)
        db.add({"data": "value"}, id="item1")

        # Check that expires_at is set correctly
        item_data = db._storage["default"]["item1"]
        assert item_data["expires_at"] is not None

    def test_no_ttl(self):
        """Test items without TTL never expire."""
        db = Database(location="memory")

        db.add({"permanent": "data"}, id="perm1")

        # Should not have expiration
        item_data = db._storage["default"]["perm1"]
        assert item_data["expires_at"] is None


class TestSchemas:
    """Test schema validation and serialization."""

    def test_pydantic_model_schema(self):
        """Test using Pydantic models as schema."""
        db = Database(location="memory")
        db.create_collection("products", schema=Product)

        # Add Pydantic model
        product = Product(name="Laptop", price=999.99, category="electronics")
        db.add(product, id="prod1", collection="products")

        # Get back as Pydantic model
        result = db.get("prod1", collection="products")
        assert isinstance(result, Product)
        assert result.name == "Laptop"
        assert result.price == 999.99

    def test_dataclass_schema(self):
        """Test using dataclasses as schema."""
        db = Database(location="memory")
        db.create_collection("users", schema=User)

        # Add dataclass
        user = User(name="Alice", email="alice@example.com", age=30)
        db.add(user, id="user1", collection="users")

        # Get back as dataclass
        result = db.get("user1", collection="users")
        assert isinstance(result, User)
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    def test_dict_data_with_schema(self):
        """Test adding dict data to schema collection."""
        db = Database(location="memory")
        db.create_collection("products", schema=Product)

        # Add dict that matches schema
        db.add({"name": "Phone", "price": 599.99}, id="prod2", collection="products")

        # Should get back as Pydantic model
        result = db.get("prod2", collection="products")
        assert isinstance(result, Product)
        assert result.name == "Phone"
        assert result.category == "general"  # default value

    def test_schema_validation_error_handling(self):
        """Test handling of schema validation errors."""
        db = Database(location="memory")
        db.create_collection("products", schema=Product)

        # Add invalid data - should not raise, but handle gracefully
        db.add({"invalid": "data"}, id="invalid", collection="products")

        # Should return raw data when validation fails
        result = db.get("invalid", collection="products")
        assert result == {"invalid": "data"}

    def test_keyvalue_collection(self):
        """Test collections without schema (key-value store)."""
        db = Database(location="memory")

        # Add various data types
        db.add("string_value", id="str1")
        db.add(42, id="num1")
        db.add([1, 2, 3], id="list1")
        db.add({"nested": {"data": True}}, id="dict1")

        # Should get back exactly as stored
        assert db.get("str1") == "string_value"
        assert db.get("num1") == 42
        assert db.get("list1") == [1, 2, 3]
        assert db.get("dict1") == {"nested": {"data": True}}


class TestPersistence:
    """Test persistence functionality with disk storage."""

    def test_persistence_across_instances(self):
        """Test that data persists across database instances."""
        # Ensure clean start
        if os.path.exists("cursives_database.db"):
            os.remove("cursives_database.db")

        # First instance
        db1 = Database(location="disk")
        db1.add({"persisted": "data"}, id="persist1")

        # Explicitly close the engine connection
        if db1._engine:
            db1._engine.dispose()

        # Second instance (should load from disk)
        db2 = Database(location="disk")
        result = db2.get("persist1")
        assert result == {"persisted": "data"}

    def test_disk_ttl_expiration(self):
        """Test TTL expiration works with disk storage."""
        db = Database(location="disk")

        # Add item with very short TTL
        db.add({"temp": "data"}, id="temp1", ttl=1)

        # Should be available immediately
        result = db.get("temp1")
        assert result == {"temp": "data"}

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired and removed
        result = db.get("temp1")
        assert result is None

    def test_disk_filters(self):
        """Test that filters work with disk storage."""
        db = Database(location="disk")

        db.add(
            {"name": "Disk User"}, id="disk1", filters={"storage": "disk", "test": True}
        )

        # Should find with matching filters
        result = db.get("disk1", filters={"storage": "disk"})
        assert result == {"name": "Disk User"}

        # Should not find with mismatched filters
        result = db.get("disk1", filters={"storage": "memory"})
        assert result is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_update_existing_item(self):
        """Test updating an existing item."""
        db = Database(location="memory")

        # Add initial item
        db.add({"version": 1}, id="update_test")

        # Update the same ID
        db.add({"version": 2}, id="update_test")

        # Should have the updated value
        result = db.get("update_test")
        assert result == {"version": 2}

    def test_update_existing_item_disk(self):
        """Test updating an existing item on disk."""
        db = Database(location="disk")

        # Add initial item
        db.add({"status": "initial"}, id="disk_update")

        # Update the same ID
        db.add({"status": "updated"}, id="disk_update")

        # Should have the updated value
        result = db.get("disk_update")
        assert result == {"status": "updated"}

    def test_empty_filters(self):
        """Test behavior with empty filters."""
        db = Database(location="memory")

        db.add({"data": "test"}, id="empty_filter", filters={})

        # Should work with empty filters dict
        result = db.get("empty_filter", filters={})
        assert result == {"data": "test"}

    def test_none_values_in_filters(self):
        """Test None values in filters."""
        db = Database(location="memory")

        db.add(
            {"data": "null_test"},
            id="null_filter",
            filters={"nullable": None, "active": True},
        )

        # Should match None values
        result = db.get("null_filter", filters={"nullable": None})
        assert result == {"data": "null_test"}

    def test_complex_nested_data(self):
        """Test storing complex nested data structures."""
        db = Database(location="memory")

        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "meta": {"role": "admin"}},
                {"id": 2, "name": "Bob", "meta": {"role": "user"}},
            ],
            "settings": {
                "theme": "dark",
                "notifications": {"email": True, "push": False},
            },
        }

        db.add(complex_data, id="complex")
        result = db.get("complex")
        assert result == complex_data

    def test_large_data_handling(self):
        """Test handling of larger data structures."""
        db = Database(location="memory")

        # Create reasonably large data
        large_data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}

        db.add(large_data, id="large")
        result = db.get("large")
        assert len(result["items"]) == 1000
        assert result["items"][500]["value"] == "item_500"


class TestConcurrency:
    """Test thread safety (basic tests)."""

    def test_concurrent_access(self):
        """Test basic concurrent access doesn't break."""
        import threading
        import concurrent.futures

        db = Database(location="memory")
        results = []
        errors = []

        def worker(worker_id):
            try:
                # Each worker adds and retrieves data
                data = {"worker": worker_id, "data": f"value_{worker_id}"}
                item_id = f"worker_{worker_id}"

                db.add(data, id=item_id)
                result = db.get(item_id)
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, e))

        # Run multiple workers concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            concurrent.futures.wait(futures)

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 20

        # Each worker should have gotten their own data back
        for worker_id, result in results:
            expected = {"worker": worker_id, "data": f"value_{worker_id}"}
            assert result == expected


if __name__ == "__main__":
    pytest.main(["-v", __file__])
