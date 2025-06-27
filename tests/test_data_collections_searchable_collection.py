import pytest
from hammad.data.collections.searchable_collection import (
    SearchableCollection as Collection,
)


def test_collection_initialization():
    """Test basic collection initialization."""
    collection = Collection("test_collection")
    assert collection.name == "test_collection"
    assert collection.schema is None
    assert collection.default_ttl is None
    assert collection._storage_backend is None


def test_collection_add_and_get():
    """Test adding and retrieving items from collection."""
    collection = Collection("test_collection")

    # Add item without ID
    collection.add("test_value")

    # Add item with specific ID
    collection.add("another_value", id="test_id")

    # Get item by ID
    result = collection.get("test_id")
    assert result == "another_value"


def test_collection_add_with_filters():
    """Test adding items with filters."""
    collection = Collection("test_collection")

    collection.add("value1", id="id1", filters={"category": "A", "status": "active"})
    collection.add("value2", id="id2", filters={"category": "B", "status": "active"})

    # Get with matching filters
    result = collection.get("id1", filters={"category": "A"})
    assert result == "value1"

    # Get with non-matching filters
    result = collection.get("id1", filters={"category": "B"})
    assert result is None


def test_collection_ttl_expiry():
    """Test TTL functionality for items."""
    import time

    collection = Collection("test_collection")

    # Add item with very short TTL
    collection.add("expires_soon", id="temp_id", ttl=1)

    # Should be available immediately
    result = collection.get("temp_id")
    assert result == "expires_soon"

    # Wait for expiry
    time.sleep(1.1)

    # Should be expired and return None
    result = collection.get("temp_id")
    assert result is None


def test_collection_query_basic():
    """Test basic query functionality."""
    collection = Collection("test_collection")

    collection.add("item1", id="1")
    collection.add("item2", id="2")
    collection.add("item3", id="3")

    # Query all items
    results = collection.query()
    assert len(results) == 3
    assert "item1" in results
    assert "item2" in results
    assert "item3" in results


def test_collection_query_with_filters():
    """Test query with filters."""
    collection = Collection("test_collection")

    collection.add("item1", id="1", filters={"category": "A"})
    collection.add("item2", id="2", filters={"category": "B"})
    collection.add("item3", id="3", filters={"category": "A"})

    # Query with filters
    results = collection.query(filters={"category": "A"})
    assert len(results) == 2
    assert "item1" in results
    assert "item3" in results


def test_collection_query_with_limit():
    """Test query with limit."""
    collection = Collection("test_collection")

    for i in range(10):
        collection.add(f"item{i}", id=str(i))

    # Query with limit
    results = collection.query(limit=5)
    assert len(results) == 5


def test_collection_search_basic():
    """Test basic search functionality."""
    collection = Collection("test_collection")

    collection.add(
        {"title": "Python Programming", "content": "Learn Python basics"}, id="1"
    )
    collection.add(
        {"title": "Java Development", "content": "Advanced Java concepts"}, id="2"
    )
    collection.add(
        {"title": "Python Web Framework", "content": "Django and Flask"}, id="3"
    )

    # Search for Python
    results = collection.query(search="Python")
    assert len(results) == 2

    # Search for Java
    results = collection.query(search="Java")
    assert len(results) == 1


def test_collection_search_phrase():
    """Test phrase search functionality."""
    collection = Collection("test_collection")

    collection.add({"content": "machine learning algorithms"}, id="1")
    collection.add({"content": "learning machine basics"}, id="2")
    collection.add({"content": "advanced machine learning"}, id="3")

    # Phrase search
    results = collection.query(search="machine learning", phrase=True)
    assert len(results) == 2  # Should match items 1 and 3


def test_collection_search_with_fields():
    """Test search with specific fields."""
    collection = Collection("test_collection")

    collection.add({"title": "Python", "content": "Java programming"}, id="1")
    collection.add({"title": "Java", "content": "Python programming"}, id="2")

    # Search only in title field
    results = collection.query(search="Python", fields=["title"])
    assert len(results) == 1


def test_collection_search_boolean_operators():
    """Test boolean search operators."""
    collection = Collection("test_collection")

    collection.add({"content": "Python machine learning"}, id="1")
    collection.add({"content": "Python web development"}, id="2")
    collection.add({"content": "Java machine learning"}, id="3")

    # AND operator
    results = collection.query(search="Python AND machine")
    assert len(results) == 1

    # OR operator
    results = collection.query(search="Python OR Java")
    assert len(results) == 3


def test_collection_search_fuzzy():
    """Test fuzzy search functionality."""
    collection = Collection("test_collection")

    collection.add({"content": "programming"}, id="1")
    collection.add({"content": "programing"}, id="2")  # typo

    # Fuzzy search should match both
    results = collection.query(search="programming", fuzzy=True)
    assert len(results) == 2


def test_collection_search_boost_fields():
    """Test field boosting in search."""
    collection = Collection("test_collection")

    collection.add({"title": "Python", "content": "Other content"}, id="1")
    collection.add({"title": "Other title", "content": "Python programming"}, id="2")

    # Boost title field
    results = collection.query(search="Python", boost_fields={"title": 2.0})

    # Item with Python in title should score higher
    assert results[0]["title"] == "Python"


def test_collection_search_min_score():
    """Test minimum score filtering."""
    collection = Collection("test_collection")

    collection.add({"content": "Python programming tutorial"}, id="1")
    collection.add({"content": "Brief Python mention"}, id="2")

    # Set minimum score to filter low-relevance results
    results = collection.query(search="Python programming", min_score=0.5)

    # Should return only high-scoring results
    assert len(results) <= 2


def test_collection_search_sort_by():
    """Test sorting search results."""
    collection = Collection("test_collection")

    collection.add({"title": "Zebra", "score": 10}, id="1")
    collection.add({"title": "Apple", "score": 20}, id="2")
    collection.add({"title": "Beta", "score": 15}, id="3")

    # Sort by title
    results = collection.query(sort_by="title", ascending=True)
    assert results[0]["title"] == "Apple"
    assert results[1]["title"] == "Beta"
    assert results[2]["title"] == "Zebra"

    # Sort by score descending
    results = collection.query(sort_by="score", ascending=False)
    assert results[0]["score"] == 20
    assert results[1]["score"] == 15
    assert results[2]["score"] == 10


def test_collection_with_schema():
    """Test collection with schema validation."""
    from dataclasses import dataclass

    @dataclass
    class User:
        name: str
        age: int

    collection = Collection("users", schema=User)

    user = User(name="Alice", age=25)
    collection.add(user, id="user1")

    result = collection.get("user1")
    assert result.name == "Alice"
    assert result.age == 25


def test_collection_repr():
    """Test collection string representation."""
    collection = Collection("test_collection")
    collection.add("test_item", id="1")

    repr_str = repr(collection)
    assert "test_collection" in repr_str
    assert "items=1" in repr_str


def test_collection_default_ttl():
    """Test collection with default TTL."""
    import time

    collection = Collection("test_collection", default_ttl=1)

    collection.add("test_value", id="test_id")

    # Should be available immediately
    result = collection.get("test_id")
    assert result == "test_value"

    # Wait for default TTL to expire
    time.sleep(1.1)

    # Should be expired
    result = collection.get("test_id")
    assert result is None


def test_collection_complex_objects():
    """Test collection with complex objects."""
    collection = Collection("complex_objects")

    complex_obj = {
        "user": {"name": "Alice", "email": "alice@example.com"},
        "metadata": {"created_at": "2024-01-01", "tags": ["python", "testing"]},
        "content": "This is some content for testing",
    }

    collection.add(complex_obj, id="complex1")

    result = collection.get("complex1")
    assert result["user"]["name"] == "Alice"
    assert "python" in result["metadata"]["tags"]

    # Test search in complex object
    results = collection.query(search="Alice")
    assert len(results) == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])
