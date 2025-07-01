import pytest
from hammad.ai.completions.types import (
    Completion,
    CompletionChunk,
    CompletionStream,
    AsyncCompletionStream,
)


def test_completion_basic():
    """Test basic Completion functionality."""
    completion = Completion(
        output="Hello, world!", model="gpt-3.5-turbo", content="Hello, world!"
    )

    assert completion.output == "Hello, world!"
    assert completion.model == "gpt-3.5-turbo"
    assert completion.content == "Hello, world!"
    assert completion.tool_calls is None
    assert completion.refusal is None
    assert completion.completion is None


def test_completion_has_tool_calls():
    """Test Completion.has_tool_calls method."""
    # Test with no tool calls
    completion = Completion(output="Hello", model="gpt-3.5-turbo")
    assert not completion.has_tool_calls()
    assert not completion.has_tool_calls("test_tool")

    # Test with tool calls
    from openai.types.chat import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message_tool_call import Function

    tool_call = ChatCompletionMessageToolCall(
        id="call_123",
        type="function",
        function=Function(name="test_tool", arguments='{"param": "value"}'),
    )

    completion_with_tools = Completion(
        output="Tool result", model="gpt-3.5-turbo", tool_calls=[tool_call]
    )

    assert completion_with_tools.has_tool_calls()
    assert completion_with_tools.has_tool_calls("test_tool")
    assert not completion_with_tools.has_tool_calls("other_tool")
    assert completion_with_tools.has_tool_calls(["test_tool", "other_tool"])


def test_completion_get_tool_call_parameters():
    """Test Completion.get_tool_call_parameters method."""
    from openai.types.chat import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message_tool_call import Function

    tool_call = ChatCompletionMessageToolCall(
        id="call_123",
        type="function",
        function=Function(
            name="test_tool", arguments='{"param": "value", "number": 42}'
        ),
    )

    completion = Completion(
        output="Tool result", model="gpt-3.5-turbo", tool_calls=[tool_call]
    )

    # Test getting parameters by tool name
    params = completion.get_tool_call_parameters("test_tool")
    assert params == {"param": "value", "number": 42}

    # Test getting parameters without specifying tool (single tool call)
    params_auto = completion.get_tool_call_parameters()
    assert params_auto == {"param": "value", "number": 42}

    # Test with non-existent tool
    params_none = completion.get_tool_call_parameters("non_existent")
    assert params_none is None


def test_completion_get_tool_call_parameters_multiple_tools():
    """Test get_tool_call_parameters with multiple tool calls."""
    from openai.types.chat import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message_tool_call import Function

    tool_call1 = ChatCompletionMessageToolCall(
        id="call_123",
        type="function",
        function=Function(name="tool1", arguments='{"param": "value1"}'),
    )
    tool_call2 = ChatCompletionMessageToolCall(
        id="call_456",
        type="function",
        function=Function(name="tool2", arguments='{"param": "value2"}'),
    )

    completion = Completion(
        output="Tool result", model="gpt-3.5-turbo", tool_calls=[tool_call1, tool_call2]
    )

    # Should raise error when multiple tools and no tool specified
    with pytest.raises(ValueError, match="Multiple tool calls found"):
        completion.get_tool_call_parameters()

    # Should work when specific tool is requested
    params1 = completion.get_tool_call_parameters("tool1")
    assert params1 == {"param": "value1"}

    params2 = completion.get_tool_call_parameters("tool2")
    assert params2 == {"param": "value2"}


def test_completion_to_message():
    """Test Completion.to_message method."""
    # Test basic completion
    completion = Completion(
        output="Hello, world!", model="gpt-3.5-turbo", content="Hello, world!"
    )

    message = completion.to_message()
    assert message == {"role": "assistant", "content": "Hello, world!"}

    # Test with structured output
    completion_structured = Completion(
        output={"key": "value"}, model="gpt-3.5-turbo", content=None
    )

    message_structured = completion_structured.to_message()
    assert message_structured["role"] == "assistant"
    assert "key" in message_structured["content"]

    # Test with refusal
    completion_refusal = Completion(
        output="Refusal", model="gpt-3.5-turbo", refusal="I cannot help with that"
    )

    message_refusal = completion_refusal.to_message()
    assert message_refusal == {
        "role": "assistant",
        "refusal": "I cannot help with that",
    }


def test_completion_to_message_with_tool_calls():
    """Test Completion.to_message with tool calls."""
    from openai.types.chat import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message_tool_call import Function

    tool_call = ChatCompletionMessageToolCall(
        id="call_123",
        type="function",
        function=Function(name="test_tool", arguments='{"param": "value"}'),
    )

    completion = Completion(
        output="Tool result",
        model="gpt-3.5-turbo",
        content="Using tool",
        tool_calls=[tool_call],
    )

    message = completion.to_message()
    assert message["role"] == "assistant"
    assert message["content"] == "Using tool"
    assert len(message["tool_calls"]) == 1
    assert message["tool_calls"][0]["id"] == "call_123"
    assert message["tool_calls"][0]["type"] == "function"
    assert message["tool_calls"][0]["function"]["name"] == "test_tool"


def test_completion_chunk():
    """Test CompletionChunk functionality."""
    # Test basic chunk
    chunk = CompletionChunk(content="Hello", model="gpt-3.5-turbo", finish_reason=None)

    assert chunk.content == "Hello"
    assert chunk.model == "gpt-3.5-turbo"
    assert not chunk.is_final
    assert bool(chunk) is True

    # Test final chunk
    final_chunk = CompletionChunk(content="", finish_reason="stop", is_final=True)

    assert final_chunk.is_final
    assert bool(final_chunk) is True  # Has finish_reason

    # Test empty chunk
    empty_chunk = CompletionChunk()
    assert bool(empty_chunk) is False


def test_completion_stream_basic():
    """Test basic CompletionStream functionality."""
    # Mock chunks for testing
    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Hello"}),
                            "finish_reason": None,
                        },
                    )
                ]
            },
        ),
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": " world"}),
                            "finish_reason": None,
                        },
                    )
                ]
            },
        ),
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "!"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        ),
    ]

    stream = CompletionStream(iter(mock_chunks), str, "gpt-3.5-turbo")

    # Test iteration
    chunks = list(stream)
    assert len(chunks) == 3
    assert chunks[0].content == "Hello"
    assert chunks[1].content == " world"
    assert chunks[2].content == "!"
    assert chunks[2].is_final

    # Test collect
    completion = stream.collect()
    assert completion.output == "Hello world!"
    assert completion.content == "Hello world!"
    assert completion.model == "gpt-3.5-turbo"


def test_completion_stream_to_completion():
    """Test CompletionStream.to_completion method."""
    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Test"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        )
    ]

    stream = CompletionStream(iter(mock_chunks), str, "gpt-3.5-turbo")

    # Should raise error if not consumed
    with pytest.raises(RuntimeError, match="Stream must be fully consumed"):
        stream.to_completion()

    # Consume stream
    list(stream)

    # Now should work
    completion = stream.to_completion()
    assert completion.output == "Test"


def test_completion_stream_to_message():
    """Test CompletionStream.to_message method."""
    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Hello"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        )
    ]

    stream = CompletionStream(iter(mock_chunks), str, "gpt-3.5-turbo")

    # Should raise error if not consumed
    with pytest.raises(RuntimeError, match="Stream must be fully consumed"):
        stream.to_message()

    # Consume stream
    list(stream)

    # Now should work
    message = stream.to_message()
    assert message["role"] == "assistant"
    assert message["content"] == "Hello"


@pytest.mark.asyncio
async def test_async_completion_stream_basic():
    """Test basic AsyncCompletionStream functionality."""

    # Mock async chunks
    class MockAsyncIterator:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.chunks)
            except StopIteration:
                raise StopAsyncIteration

    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Hello"}),
                            "finish_reason": None,
                        },
                    )
                ]
            },
        ),
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": " async"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        ),
    ]

    async_iter = MockAsyncIterator(mock_chunks)
    stream = AsyncCompletionStream(async_iter, str, "gpt-3.5-turbo")

    # Test async iteration
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].content == "Hello"
    assert chunks[1].content == " async"
    assert chunks[1].is_final

    # Test async collect
    completion = await stream.collect()
    assert completion.output == "Hello async"
    assert completion.content == "Hello async"


@pytest.mark.asyncio
async def test_async_completion_stream_to_completion():
    """Test AsyncCompletionStream.to_completion method."""

    class MockAsyncIterator:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.chunks)
            except StopIteration:
                raise StopAsyncIteration

    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Test"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        )
    ]

    async_iter = MockAsyncIterator(mock_chunks)
    stream = AsyncCompletionStream(async_iter, str, "gpt-3.5-turbo")

    # Should raise error if not consumed
    with pytest.raises(RuntimeError, match="Stream must be fully consumed"):
        await stream.to_completion()

    # Consume stream
    async for _ in stream:
        pass

    # Now should work
    completion = await stream.to_completion()
    assert completion.output == "Test"


@pytest.mark.asyncio
async def test_async_completion_stream_to_message():
    """Test AsyncCompletionStream.to_message method."""

    class MockAsyncIterator:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.chunks)
            except StopIteration:
                raise StopAsyncIteration

    mock_chunks = [
        type(
            "MockChunk",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "delta": type("Delta", (), {"content": "Hello"}),
                            "finish_reason": "stop",
                        },
                    )
                ]
            },
        )
    ]

    async_iter = MockAsyncIterator(mock_chunks)
    stream = AsyncCompletionStream(async_iter, str, "gpt-3.5-turbo")

    # Should raise error if not consumed
    with pytest.raises(RuntimeError, match="Stream must be fully consumed"):
        await stream.to_message()

    # Consume stream
    async for _ in stream:
        pass

    # Now should work
    message = await stream.to_message()
    assert message["role"] == "assistant"
    assert message["content"] == "Hello"


def test_completion_stream_instructor_mode():
    """Test CompletionStream with instructor mode (structured output)."""
    # Mock instructor chunks
    mock_chunks = [
        type("PartialModel", (), {"field": "partial", "_is_final": False})(),
        type("CompleteModel", (), {"field": "complete", "_is_final": True})(),
    ]

    # Use a non-str type to trigger instructor mode
    from pydantic import BaseModel

    class TestModel(BaseModel):
        field: str

    stream = CompletionStream(iter(mock_chunks), TestModel, "gpt-3.5-turbo")

    chunks = list(stream)
    assert len(chunks) == 2
    assert chunks[0].output.field == "partial"
    assert not chunks[0].is_final
    assert chunks[1].output.field == "complete"
    assert chunks[1].is_final

    # Test collect for instructor mode
    completion = stream.collect()
    assert completion.output.field == "complete"
    assert completion.content is None  # No content for structured output


@pytest.mark.asyncio
async def test_async_completion_stream_instructor_mode():
    """Test AsyncCompletionStream with instructor mode."""

    class MockAsyncIterator:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.chunks)
            except StopIteration:
                raise StopAsyncIteration

    # Mock instructor chunks
    mock_chunks = [
        type("PartialModel", (), {"field": "partial", "_is_final": False})(),
        type("CompleteModel", (), {"field": "complete", "_is_final": True})(),
    ]

    from pydantic import BaseModel

    class TestModel(BaseModel):
        field: str

    async_iter = MockAsyncIterator(mock_chunks)
    stream = AsyncCompletionStream(async_iter, TestModel, "gpt-3.5-turbo")

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].output.field == "partial"
    assert chunks[1].output.field == "complete"

    completion = await stream.collect()
    assert completion.output.field == "complete"
    assert completion.content is None


if __name__ == "__main__":
    pytest.main(["-v", __file__])
