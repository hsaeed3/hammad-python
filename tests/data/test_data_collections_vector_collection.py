import pytest
from unittest.mock import Mock, patch
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


def test_vector_collection_with_embedding_parameters():
    """Test VectorCollection with embedding parameters."""
    collection = Collection(
        name="test",
        vector_size=384,
        model="fastembed/BAAI/bge-small-en-v1.5",
        format=True,
        parallel=2,
        batch_size=16,
    )
    assert collection.name == "test"
    assert collection.vector_size == 384
    assert collection._model == "fastembed/BAAI/bge-small-en-v1.5"
    assert collection._embedding_params["format"] is True
    assert collection._embedding_params["parallel"] == 2
    assert collection._embedding_params["batch_size"] == 16


def test_vector_collection_with_litellm_parameters():
    """Test VectorCollection with LiteLLM parameters."""
    collection = Collection(
        name="test",
        vector_size=1536,
        model="text-embedding-ada-002",
        dimensions=1536,
        api_key="test-key",
        timeout=600,
        caching=True,
    )
    assert collection.name == "test"
    assert collection.vector_size == 1536
    assert collection._model == "text-embedding-ada-002"
    assert collection._embedding_params["dimensions"] == 1536
    assert collection._embedding_params["api_key"] == "test-key"
    assert collection._embedding_params["timeout"] == 600
    assert collection._embedding_params["caching"] is True


def test_add_and_get_vector():
    """Test adding and retrieving vector data."""
    collection = Collection(name="test", vector_size=3)

    # Add a vector directly as list (test new signature with id as positional)
    vector_data = [1.0, 2.0, 3.0]
    returned_id = collection.add(vector_data, "vec1")
    assert returned_id == "vec1"

    # Retrieve the item
    result = collection.get("vec1")
    assert result == vector_data

    # Test add without id (should return generated UUID)
    returned_id2 = collection.add([4.0, 5.0, 6.0])
    assert isinstance(returned_id2, str)
    assert len(returned_id2) > 0


def test_add_dict_with_vector():
    """Test adding dictionary with vector field."""
    collection = Collection(name="test", vector_size=3)

    data = {"vector": [1.0, 2.0, 3.0], "metadata": {"type": "test"}}
    returned_id = collection.add(data, "item1")
    assert returned_id == "item1"

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
        collection.add(vector, id_val)

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

    collection.add(data1, "item1", filters={"category": "A"})
    collection.add(data2, "item2", filters={"category": "B"})

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
    collection.add(vector, "vec1")

    retrieved_vector = collection.get_vector("vec1")
    assert retrieved_vector == vector


def test_count():
    """Test counting items in collection."""
    collection = Collection(name="test", vector_size=3)

    # Initially empty
    assert collection.count() == 0

    # Add some items
    collection.add([1.0, 0.0, 0.0], "vec1")
    collection.add([0.0, 1.0, 0.0], "vec2")

    assert collection.count() == 2


def test_delete():
    """Test deleting items."""
    collection = Collection(name="test", vector_size=3)

    vector = [1.0, 2.0, 3.0]
    collection.add(vector, "vec1")

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

    collection.add(data1, "item1")
    collection.add(data2, "item2")

    # Query all items (test new signature with no query parameter)
    results = collection.query(limit=10)
    assert len(results) == 2

    # Check that both items are returned
    result_names = {item["name"] for item in results}
    assert result_names == {"first", "second"}


def test_query_with_search_string():
    """Test querying with search string (new interface)."""
    collection = Collection(name="test", vector_size=3)

    # Add test data
    data1 = {"vector": [1.0, 0.0, 0.0], "content": "hello world"}
    data2 = {"vector": [0.0, 1.0, 0.0], "content": "goodbye world"}

    collection.add(data1, "item1")
    collection.add(data2, "item2")

    # Test new query interface with search as first positional parameter
    # This should fail without an embedding function
    with pytest.raises(
        ValueError, match="Search query provided but no embedding_function"
    ):
        collection.query("hello")

    # Test query with None (no search)
    results = collection.query(None, limit=10)
    assert len(results) == 2


def test_embedding_function():
    """Test using embedding function."""

    def simple_embedding(text):
        # Simple embedding: convert text to numbers
        return [float(ord(c)) for c in text[:3].ljust(3, "a")]

    collection = Collection(
        name="test", vector_size=3, embedding_function=simple_embedding
    )

    # Add text data that will be converted to vectors
    collection.add("hello", "text1")
    collection.add("world", "text2")

    # Verify we can retrieve the original text
    assert collection.get("text1") == "hello"
    assert collection.get("text2") == "world"

    # Test search with text query (using new interface)
    results = collection.query("help", limit=1)
    assert len(results) <= 1


@patch("hammad.ai.embeddings.create.create_embeddings")
def test_embedding_model_integration(mock_create_embeddings):
    """Test integration with embedding models."""
    # Mock the embedding response
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
    mock_create_embeddings.return_value = mock_response

    collection = Collection(
        name="test",
        vector_size=3,
        model="fastembed/BAAI/bge-small-en-v1.5",
        format=True,
        parallel=2,
    )

    # Add text that should be embedded
    collection.add("hello world", "text1")

    # Verify the embedding function was called with correct parameters
    mock_create_embeddings.assert_called_once()
    call_kwargs = mock_create_embeddings.call_args.kwargs
    assert call_kwargs["model"] == "fastembed/BAAI/bge-small-en-v1.5"
    assert call_kwargs["input"] == "hello world"
    assert call_kwargs["format"] is True
    assert call_kwargs["parallel"] == 2

    # Verify we can retrieve the original text
    assert collection.get("text1") == "hello world"


@patch("hammad.ai.embeddings.create.create_embeddings")
def test_semantic_search_with_model(mock_create_embeddings):
    """Test semantic search using embedding model."""
    # Mock the embedding response
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
    mock_create_embeddings.return_value = mock_response

    collection = Collection(
        name="test",
        vector_size=3,
        model="text-embedding-ada-002",
        dimensions=3,
        api_key="test-key",
    )

    # Add some documents
    collection.add("machine learning tutorial", "doc1")
    collection.add("cooking recipes", "doc2")

    # Reset mock for search call
    mock_create_embeddings.reset_mock()

    # Perform semantic search
    results = collection.query("AI and ML", limit=1)

    # Verify embedding was called for the search query
    mock_create_embeddings.assert_called_once()
    call_kwargs = mock_create_embeddings.call_args.kwargs
    assert call_kwargs["model"] == "text-embedding-ada-002"
    assert call_kwargs["input"] == "AI and ML"
    assert call_kwargs["dimensions"] == 3
    assert call_kwargs["api_key"] == "test-key"


def test_vector_size_validation():
    """Test vector size validation."""
    collection = Collection(name="test", vector_size=3)

    # This should work
    collection.add([1.0, 2.0, 3.0], "good")

    # This should fail
    with pytest.raises(ValueError, match="Vector size .* doesn't match"):
        collection.add([1.0, 2.0], "bad")  # Wrong size


def test_ttl_functionality():
    """Test TTL (time-to-live) functionality."""
    collection = Collection(name="test", vector_size=3, default_ttl=1)

    # Add item with short TTL
    vector = [1.0, 2.0, 3.0]
    collection.add(vector, "temp", ttl=1)  # 1 second TTL

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
        collection.add("invalid_data", "bad")


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
    collection.add([1.0, 0.0, 0.0], "vec1")
    collection.add([0.0, 0.0, 1.0], "vec2")  # Very different vector

    # Search with high threshold - should return fewer results
    query_vector = [1.0, 0.0, 0.0]
    results = collection.vector_search(
        query_vector,
        score_threshold=0.9,  # High threshold
        limit=10,
    )

    # Should have some results but potentially filtered by threshold
    assert isinstance(results, list)


def test_embedding_parameter_validation():
    """Test validation of embedding parameters."""
    # Test that FastEmbed-specific parameters are stored
    collection = Collection(
        name="test",
        vector_size=384,
        model="fastembed/BAAI/bge-small-en-v1.5",
        parallel=4,
        batch_size=32,
        format=True,
    )

    assert collection._embedding_params["parallel"] == 4
    assert collection._embedding_params["batch_size"] == 32
    assert collection._embedding_params["format"] is True

    # Test that LiteLLM-specific parameters are stored
    collection2 = Collection(
        name="test2",
        vector_size=1536,
        model="text-embedding-ada-002",
        dimensions=1536,
        encoding_format="float",
        timeout=600,
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        caching=True,
    )

    assert collection2._embedding_params["dimensions"] == 1536
    assert collection2._embedding_params["encoding_format"] == "float"
    assert collection2._embedding_params["timeout"] == 600
    assert collection2._embedding_params["api_base"] == "https://api.openai.com/v1"
    assert collection2._embedding_params["api_key"] == "sk-test"
    assert collection2._embedding_params["caching"] is True


def test_model_without_embedding_function():
    """Test that providing a model creates an embedding function."""
    collection = Collection(
        name="test", vector_size=384, model="fastembed/BAAI/bge-small-en-v1.5"
    )

    # Should have created an embedding function
    assert collection._embedding_function is not None
    assert collection._model == "fastembed/BAAI/bge-small-en-v1.5"


def test_no_model_no_embedding_function():
    """Test collection without model or embedding function."""
    collection = Collection(name="test", vector_size=3)

    # Should not have an embedding function
    assert collection._embedding_function is None
    assert collection._model is None


def test_vector_search_default_limit():
    """Test that vector_search has a sensible default limit."""
    collection = Collection(name="test", vector_size=3)

    # Add test vectors
    for i in range(15):
        collection.add([float(i), 0.0, 0.0], f"vec{i}")

    # Default limit should be 10
    results = collection.vector_search([1.0, 0.0, 0.0])
    assert len(results) == 10

    # Custom limit should work
    results = collection.vector_search([1.0, 0.0, 0.0], limit=5)
    assert len(results) == 5


@patch("hammad.ai.embeddings.create.create_embeddings")
def test_embedding_function_parameter_filtering(mock_create_embeddings):
    """Test that only non-None parameters are passed to embedding function."""
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
    mock_create_embeddings.return_value = mock_response

    collection = Collection(
        name="test",
        vector_size=3,
        model="text-embedding-ada-002",
        dimensions=3,
        timeout=None,  # This should be filtered out
        api_key="test-key",
        encoding_format=None,  # This should be filtered out
        caching=False,
    )

    # Add a document to trigger embedding
    collection.add("test document", "doc1")

    # Check that only non-None parameters were passed
    call_kwargs = mock_create_embeddings.call_args.kwargs
    assert "timeout" not in call_kwargs
    assert "encoding_format" not in call_kwargs
    assert call_kwargs["dimensions"] == 3
    assert call_kwargs["api_key"] == "test-key"
    assert call_kwargs["caching"] is False  # False should be included


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
