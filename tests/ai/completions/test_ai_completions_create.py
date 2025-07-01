import pytest
import asyncio
from pydantic import BaseModel
from hammad.ai.completions.create import (
    create_completion,
    async_create_completion as create_async_completion,
)
from hammad.ai.completions.types import (
    Completion,
    CompletionStream,
    AsyncCompletionStream,
)


def test_create_completion_normal():
    response = create_completion(
        messages=[{"role": "user", "content": "hi"}], model="openai/gpt-4o-mini"
    )

    print(response)

    assert response.content is not None
    assert response.model is not None


def test_create_completion_string_message():
    response = create_completion(messages="hi", model="openai/gpt-4o-mini")

    print(response)

    assert response.content is not None
    assert response.model is not None


def test_create_completion_formatted_string_message():
    response = create_completion(
        messages="""
[system]You are a helpful assistant who only speaks in Haikus.
[user]What is the capital of France?
""",
        model="openai/gpt-4o-mini",
    )

    print(response)

    assert response.content is not None
    assert response.model is not None


def test_create_completion_structured_pydantic():
    class User(BaseModel):
        name: str
        age: int

    response = create_completion(
        messages=[{"role": "user", "content": "Extract John is 25 years old"}],
        model="openai/gpt-4o-mini",
        type=User,
    )

    print(response)

    assert response.output is not None
    assert response.output.name == "John"
    assert response.output.age == 25


def test_create_completion_structured_non_pydantic():
    response = create_completion(
        messages=[
            {
                "role": "user",
                "content": "How many apples do i have if i start with 10 and eat 2?",
            }
        ],
        model="openai/gpt-4o-mini",
        type=int,
    )

    print(response)

    assert response.output is not None
    assert response.output == 8


# Async tests
@pytest.mark.asyncio
async def test_create_async_completion_normal():
    response = await create_async_completion(
        messages=[{"role": "user", "content": "hi"}], model="openai/gpt-4o-mini"
    )

    print(response)

    assert response.content is not None
    assert response.model is not None


@pytest.mark.asyncio
async def test_create_async_completion_structured_pydantic():
    class User(BaseModel):
        name: str
        age: int

    response = await create_async_completion(
        messages=[{"role": "user", "content": "Extract John is 25 years old"}],
        model="openai/gpt-4o-mini",
        type=User,
    )

    print(response)

    assert response.output is not None
    assert response.output.name == "John"
    assert response.output.age == 25


# Streaming tests
def test_create_completion_stream():
    stream = create_completion(
        messages=[{"role": "user", "content": "Tell me a short story"}],
        model="openai/gpt-4o-mini",
        stream=True,
    )

    assert isinstance(stream, CompletionStream)

    # Consume stream and check chunks
    chunks = []
    for chunk in stream:
        chunks.append(chunk)
        print(f"Chunk: {chunk.content}")

    assert len(chunks) > 0

    # Test conversion methods
    completion = stream.to_completion()
    assert isinstance(completion, Completion)
    assert completion.content is not None

    message = stream.to_message()
    assert message["role"] == "assistant"
    assert message["content"] is not None


@pytest.mark.asyncio
async def test_create_async_completion_stream():
    stream = await create_async_completion(
        messages=[{"role": "user", "content": "Tell me a short story"}],
        model="openai/gpt-4o-mini",
        stream=True,
    )

    assert isinstance(stream, AsyncCompletionStream)

    # Consume stream and check chunks
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
        print(f"Async Chunk: {chunk.content}")

    assert len(chunks) > 0

    # Test conversion methods
    completion = await stream.to_completion()
    assert isinstance(completion, Completion)
    assert completion.content is not None

    message = await stream.to_message()
    assert message["role"] == "assistant"
    assert message["content"] is not None


def test_create_completion_structured_stream():
    class Summary(BaseModel):
        title: str
        points: list[str]

    stream = create_completion(
        messages=[
            {
                "role": "user",
                "content": "Summarize: Machine learning is a subset of AI that enables computers to learn without explicit programming.",
            }
        ],
        model="openai/gpt-4o-mini",
        type=Summary,
        stream=True,
    )

    assert isinstance(stream, CompletionStream)

    # Consume stream
    chunks = []
    for chunk in stream:
        chunks.append(chunk)
        if chunk.output:
            print(f"Structured chunk: {chunk.output}")

    assert len(chunks) > 0

    # Test final completion
    completion = stream.to_completion()
    assert isinstance(completion.output, Summary)
    assert completion.output.title is not None


@pytest.mark.asyncio
async def test_create_async_completion_structured_stream():
    class Summary(BaseModel):
        title: str
        points: list[str]

    stream = await create_async_completion(
        messages=[
            {
                "role": "user",
                "content": "Summarize: Machine learning is a subset of AI that enables computers to learn without explicit programming.",
            }
        ],
        model="openai/gpt-4o-mini",
        type=Summary,
        stream=True,
    )

    assert isinstance(stream, AsyncCompletionStream)

    # Consume stream
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
        if chunk.output:
            print(f"Async structured chunk: {chunk.output}")

    assert len(chunks) > 0

    # Test final completion
    completion = await stream.to_completion()
    assert isinstance(completion.output, Summary)
    assert completion.output.title is not None


if __name__ == "__main__":
    pytest.main(["-v", __file__])
