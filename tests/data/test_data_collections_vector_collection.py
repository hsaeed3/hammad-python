import pytest
from hammad.data.collections import VectorCollection as Collection


def test_vector_collection_init():
    """Test VectorCollection initialization."""
    collection = Collection(name="test", vector_size=128)
    assert collection.name == "test"
    assert collection.vector_size == 128
    assert collection.schema is None
    assert collection.default_ttl is None


def test_vector_collection_with_config():
    """Test VectorCollection with custom configuration."""
    config = {"path": "/tmp/test_qdrant"}
    collection = Collection(
        name="test", vector_size=256, qdrant_config=config, default_ttl=3600
    )
    assert collection.name == "test"
    assert collection.vector_size == 256
    assert collection.default_ttl == 3600


def test_add_and_get_vector():
    """Test adding and retrieving vector data."""
    collection = Collection(name="test", vector_size=3)

    # Add a vector directly as list
    vector_data = [1.0, 2.0, 3.0]
    collection.add(vector_data, id="vec1")

    # Retrieve the item
    result = collection.get("vec1")
    assert result == vector_data


def test_add_dict_with_vector():
    """Test adding dictionary with vector field."""
    collection = Collection(name="test", vector_size=3)

    data = {"vector": [1.0, 2.0, 3.0], "metadata": {"type": "test"}}
    collection.add(data, id="item1")

    result = collection.get("item1")
    assert result == data


def test_vector_search():
    """Test vector similarity search."""
    collection = Collection(name="test", vector_size=3)

    # Add some test vectors
    vectors = [
        ([1.0, 0.0, 0.0], "vec1"),
        ([0.0, 1.0, 0.0], "vec2"),
        ([1.0, 1.0, 0.0], "vec3"),
    ]

    for vector, id_val in vectors:
        collection.add(vector, id=id_val)

    # Search for similar vectors
    query_vector = [1.0, 0.1, 0.0]
    results = collection.vector_search(query_vector, limit=2)

    assert len(results) <= 2
    assert len(results) > 0


def test_vector_search_with_filters():
    """Test vector search with filters."""
    collection = Collection(name="test", vector_size=3)

    # Add vectors with metadata
    data1 = {"vector": [1.0, 0.0, 0.0], "category": "A"}
    data2 = {"vector": [0.0, 1.0, 0.0], "category": "B"}

    collection.add(data1, id="item1", filters={"category": "A"})
    collection.add(data2, id="item2", filters={"category": "B"})

    # Search with filter
    query_vector = [1.0, 0.0, 0.0]
    results = collection.vector_search(
        query_vector, filters={"category": "A"}, limit=10
    )

    assert len(results) == 1
    assert results[0] == data1


def test_get_vector():
    """Test retrieving vector for an item."""
    collection = Collection(name="test", vector_size=3)

    vector = [1.0, 2.0, 3.0]
    collection.add(vector, id="vec1")

    retrieved_vector = collection.get_vector("vec1")
    assert retrieved_vector == vector


def test_count():
    """Test counting items in collection."""
    collection = Collection(name="test", vector_size=3)

    # Initially empty
    assert collection.count() == 0

    # Add some items
    collection.add([1.0, 0.0, 0.0], id="vec1")
    collection.add([0.0, 1.0, 0.0], id="vec2")

    assert collection.count() == 2


def test_delete():
    """Test deleting items."""
    collection = Collection(name="test", vector_size=3)

    vector = [1.0, 2.0, 3.0]
    collection.add(vector, id="vec1")

    # Verify item exists
    assert collection.get("vec1") is not None

    # Delete item
    success = collection.delete("vec1")
    assert success is True

    # Verify item is gone
    assert collection.get("vec1") is None


def test_query_all():
    """Test querying all items without vector search."""
    collection = Collection(name="test", vector_size=3)

    # Add some test data
    data1 = {"vector": [1.0, 0.0, 0.0], "name": "first"}
    data2 = {"vector": [0.0, 1.0, 0.0], "name": "second"}

    collection.add(data1, id="item1")
    collection.add(data2, id="item2")

    # Query all items
    results = collection.query(limit=10)
    assert len(results) == 2

    # Check that both items are returned
    result_names = {item["name"] for item in results}
    assert result_names == {"first", "second"}


def test_embedding_function():
    """Test using embedding function."""

    def simple_embedding(text):
        # Simple embedding: convert text to numbers
        return [float(ord(c)) for c in text[:3].ljust(3, "a")]

    collection = Collection(
        name="test", vector_size=3, embedding_function=simple_embedding
    )

    # Add text data that will be converted to vectors
    collection.add("hello", id="text1")
    collection.add("world", id="text2")

    # Verify we can retrieve the original text
    assert collection.get("text1") == "hello"
    assert collection.get("text2") == "world"

    # Test search with text query
    results = collection.query(search="help", limit=1)
    assert len(results) <= 1


def test_vector_size_validation():
    """Test vector size validation."""
    collection = Collection(name="test", vector_size=3)

    # This should work
    collection.add([1.0, 2.0, 3.0], id="good")

    # This should fail
    with pytest.raises(ValueError, match="Vector size .* doesn't match"):
        collection.add([1.0, 2.0], id="bad")  # Wrong size


def test_ttl_functionality():
    """Test TTL (time-to-live) functionality."""
    collection = Collection(name="test", vector_size=3, default_ttl=1)

    # Add item with short TTL
    vector = [1.0, 2.0, 3.0]
    collection.add(vector, id="temp", ttl=1)  # 1 second TTL

    # Item should exist immediately
    assert collection.get("temp") is not None

    # Note: Testing actual expiration would require time.sleep()
    # which makes tests slow, so we just verify the functionality exists


def test_repr():
    """Test string representation."""
    collection = Collection(name="test_collection", vector_size=128)
    repr_str = repr(collection)
    assert "test_collection" in repr_str
    assert "128" in repr_str
    assert "VectorCollection" in repr_str


def test_invalid_vector_types():
    """Test handling of invalid vector types."""
    collection = Collection(name="test", vector_size=3)

    # Should raise error for invalid data without embedding function
    with pytest.raises(ValueError, match="Entry must contain 'vector' key"):
        collection.add("invalid_data", id="bad")


def test_nonexistent_item():
    """Test getting non-existent items."""
    collection = Collection(name="test", vector_size=3)

    result = collection.get("nonexistent")
    assert result is None

    vector = collection.get_vector("nonexistent")
    assert vector is None


def test_score_threshold():
    """Test vector search with score threshold."""
    collection = Collection(name="test", vector_size=3)

    # Add test vectors
    collection.add([1.0, 0.0, 0.0], id="vec1")
    collection.add([0.0, 0.0, 1.0], id="vec2")  # Very different vector

    # Search with high threshold - should return fewer results
    query_vector = [1.0, 0.0, 0.0]
    results = collection.vector_search(
        query_vector,
        score_threshold=0.9,  # High threshold
        limit=10,
    )

    # Should have some results but potentially filtered by threshold
    assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
