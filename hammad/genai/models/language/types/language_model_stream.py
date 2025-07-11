"""hammad.genai.models.language.types.language_model_stream"""

import asyncio
from typing import (
    List,
    Type,
    TypeVar,
    Generic,
    Iterator,
    AsyncIterator,
    Optional,
    Any,
    Callable,
    Dict,
    Union,
)

from .....typing import get_origin, get_args
from ....types.base import BaseGenAIModelStream

from .language_model_response import LanguageModelResponse
from .language_model_response_chunk import LanguageModelResponseChunk

__all__ = [
    "LanguageModelStream",
    "InstructorStreamCollector",
    "InstructorStreamWrapper",
    "AsyncInstructorStreamWrapper",
    "StreamingChunkProcessor",
]

T = TypeVar("T")


class InstructorStreamCollector:
    """Collector for instructor streaming responses using hooks."""

    def __init__(self):
        self.raw_chunks = []
        self.completion_responses = []
        self.last_response = None
        self.error = None

    def on_completion_response(self, response):
        """Hook handler for completion responses."""
        self.completion_responses.append(response)

    def on_completion_error(self, error):
        """Hook handler for completion errors."""
        self.error = error

    def add_chunk(self, chunk):
        """Add a raw chunk to the collector."""
        self.raw_chunks.append(chunk)

    def get_raw_content(self):
        """Get raw content from completion responses."""
        if self.completion_responses:
            last_response = self.completion_responses[-1]
            if hasattr(last_response, "choices") and last_response.choices:
                choice = last_response.choices[0]
                if hasattr(choice, "message"):
                    return getattr(choice.message, "content", None)
        return None

    def get_raw_completion(self):
        """Get the raw completion object."""
        return self.completion_responses[-1] if self.completion_responses else None

    def get_tool_calls(self):
        """Get tool calls from completion responses."""
        if self.completion_responses:
            last_response = self.completion_responses[-1]
            if hasattr(last_response, "choices") and last_response.choices:
                choice = last_response.choices[0]
                if hasattr(choice, "message"):
                    return getattr(choice.message, "tool_calls", None)
        return None


class StreamingChunkProcessor:
    """Process streaming chunks to extract only new content."""

    def __init__(self, output_type: Type[T], response_field_name: Optional[str] = None):
        self.output_type = output_type
        self.response_field_name = response_field_name
        self.previous_chunk = None
        self.previous_content = ""

    def process_chunk(self, chunk: Any) -> Optional[str]:
        """Process a chunk and return only the new content."""
        # Handle list types (e.g., list[str])
        from .....typing import get_origin

        origin = get_origin(self.output_type)

        if origin is list:
            return self._process_list_chunk(chunk)
        elif self.response_field_name and hasattr(chunk, self.response_field_name):
            return self._process_field_chunk(chunk)
        else:
            return self._process_simple_chunk(chunk)

    def _process_list_chunk(self, chunk: Any) -> Optional[str]:
        """Process chunks for list types."""
        current_list = []

        if isinstance(chunk, list):
            current_list = chunk
        elif hasattr(chunk, "value") and isinstance(chunk.value, list):
            current_list = chunk.value
        elif hasattr(chunk, self.response_field_name) and isinstance(
            getattr(chunk, self.response_field_name), list
        ):
            current_list = getattr(chunk, self.response_field_name)

        if not current_list:
            return None

        # For list types, return only new items
        if self.previous_chunk is None:
            # First chunk - return the last item
            if current_list:
                self.previous_chunk = current_list
                return str(current_list[-1])
        else:
            # Subsequent chunks - return only new items
            prev_list = (
                self.previous_chunk if isinstance(self.previous_chunk, list) else []
            )
            prev_len = len(prev_list)

            if len(current_list) > prev_len:
                new_items = current_list[prev_len:]
                self.previous_chunk = current_list
                if new_items:
                    return str(new_items[-1])

        return None

    def _process_field_chunk(self, chunk: Any) -> Optional[str]:
        """Process chunks with a specific response field."""
        if not hasattr(chunk, self.response_field_name):
            return None

        field_value = getattr(chunk, self.response_field_name)

        if isinstance(field_value, str):
            # For string fields, return only new content
            if self.previous_chunk is None:
                self.previous_chunk = chunk
                self.previous_content = field_value
                return field_value
            else:
                prev_value = self.previous_content
                current_value = field_value

                if current_value.startswith(prev_value):
                    new_content = current_value[len(prev_value) :]
                    self.previous_chunk = chunk
                    self.previous_content = current_value
                    return new_content if new_content else None
                else:
                    self.previous_chunk = chunk
                    self.previous_content = current_value
                    return current_value
        elif isinstance(field_value, list):
            # For list fields in response field
            if self.previous_chunk is None:
                self.previous_chunk = chunk
                if field_value:
                    return str(field_value[-1])
            else:
                prev_field = getattr(self.previous_chunk, self.response_field_name, [])
                prev_len = len(prev_field) if isinstance(prev_field, list) else 0

                if len(field_value) > prev_len:
                    new_items = field_value[prev_len:]
                    self.previous_chunk = chunk
                    if new_items:
                        return str(new_items[-1])

        return None

    def _process_simple_chunk(self, chunk: Any) -> Optional[str]:
        """Process simple chunks without response fields."""
        if hasattr(chunk, "value"):
            value = chunk.value
            if isinstance(value, str):
                if self.previous_content:
                    if value.startswith(self.previous_content):
                        new_content = value[len(self.previous_content) :]
                        self.previous_content = value
                        return new_content if new_content else None
                    else:
                        self.previous_content = value
                        return value
                else:
                    self.previous_content = value
                    return value
        elif isinstance(chunk, str):
            if self.previous_content:
                if chunk.startswith(self.previous_content):
                    new_content = chunk[len(self.previous_content) :]
                    self.previous_content = chunk
                    return new_content if new_content else None
                else:
                    self.previous_content = chunk
                    return chunk
            else:
                self.previous_content = chunk
                return chunk
        elif self.output_type in (int, float, bool):
            # For primitive types, return string representation
            return str(chunk)

        return None


class InstructorStreamWrapper:
    """Wrapper for instructor streams that collects raw responses via hooks."""

    def __init__(self, stream: Iterator[Any], collector: InstructorStreamCollector):
        self._stream = stream
        self.collector = collector

    def __iter__(self):
        return self

    def __next__(self):
        chunk = next(self._stream)
        self.collector.add_chunk(chunk)
        return chunk

    def get_raw_content(self):
        return self.collector.get_raw_content()

    def get_raw_completion(self):
        return self.collector.get_raw_completion()

    def get_tool_calls(self):
        return self.collector.get_tool_calls()


class AsyncInstructorStreamWrapper:
    """Async wrapper for instructor streams that collects raw responses via hooks."""

    def __init__(
        self, stream: AsyncIterator[Any], collector: InstructorStreamCollector
    ):
        self._stream = stream
        self.collector = collector

    def __aiter__(self):
        return self

    async def __anext__(self):
        chunk = await self._stream.__anext__()
        self.collector.add_chunk(chunk)
        return chunk

    def get_raw_content(self):
        return self.collector.get_raw_content()

    def get_raw_completion(self):
        return self.collector.get_raw_completion()

    def get_tool_calls(self):
        return self.collector.get_tool_calls()


class LanguageModelStream(
    BaseGenAIModelStream[LanguageModelResponseChunk[T]], Generic[T]
):
    """Unified stream wrapper for language model streaming.

    This class provides a unified interface for both sync and async streaming responses
    from both LiteLLM and Instructor, handling the different chunk formats and providing
    consistent access patterns. It inherits from BaseGenAIModelStream and manages
    both sync and async streaming in a single class.
    """

    def __init__(
        self,
        stream: Union[Iterator[Any], AsyncIterator[Any]],
        output_type: Type[T] = str,
        model: Optional[str] = None,
        response_field_name: Optional[str] = None,
    ):
        """Initialize the stream.

        Args:
            stream: The underlying stream iterator (sync or async)
            output_type: The expected output type
            model: The model name
            response_field_name: The field name for structured outputs
        """
        # Initialize base class
        super().__init__(
            type="language_model",
            model=model or "unknown",
            stream=stream,
        )

        self._stream = stream
        self._output_type = output_type
        self._model = model
        self._response_field_name = response_field_name
        self._chunks: List[LanguageModelResponseChunk[T]] = []
        self._final_output: Optional[T] = None
        self._is_instructor = output_type != str
        self._is_consumed = False
        self._previous_chunk_output = None
        self._is_async = hasattr(stream, "__anext__")
        self._full_content = ""

    def __iter__(self) -> Iterator[LanguageModelResponseChunk[T]]:
        """Iterate over response chunks (sync mode)."""
        if self._is_async:
            # This is a workaround to allow sync iteration over an async stream
            # It's not ideal, but it works for simple cases.
            # A better solution would be to use a dedicated sync entrypoint
            # if this is a common use case.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            async_iter = self.__aiter__()
            while True:
                try:
                    # We are calling the async __anext__ which returns a processed chunk
                    yield loop.run_until_complete(async_iter.__anext__())
                except StopAsyncIteration:
                    break
            return

        for chunk in self._stream:
            response_chunk = self._process_chunk(chunk)
            if response_chunk:
                self._chunks.append(response_chunk)
                yield response_chunk
        self._is_consumed = True

    def __aiter__(self) -> AsyncIterator[LanguageModelResponseChunk[T]]:
        """Async iterate over response chunks (async mode)."""
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async iteration on sync stream. Use regular for loop instead."
            )
        return self

    async def __anext__(self) -> LanguageModelResponseChunk[T]:
        """Get the next response chunk (async mode)."""
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async iteration on sync stream. Use regular for loop instead."
            )

        try:
            chunk = await self._stream.__anext__()
            response_chunk = self._process_chunk(chunk)
            if response_chunk:
                self._chunks.append(response_chunk)
                return response_chunk
            else:
                return await self.__anext__()  # Skip empty chunks
        except StopAsyncIteration:
            self._is_consumed = True
            raise StopAsyncIteration

    def _process_chunk(self, chunk: Any) -> Optional[LanguageModelResponseChunk[T]]:
        """Process a raw chunk into a LanguageModelResponseChunk."""
        if self._is_instructor:
            # Handle instructor streaming (Partial/Iterable)

            # Use the chunk processor to get only new content
            if not hasattr(self, "_chunk_processor"):
                self._chunk_processor = StreamingChunkProcessor(
                    self._output_type, self._response_field_name
                )

            content = self._chunk_processor.process_chunk(chunk)

            # Extract the proper output value
            if self._response_field_name and hasattr(chunk, self._response_field_name):
                output_value = getattr(chunk, self._response_field_name)
            else:
                output_value = chunk

            return LanguageModelResponseChunk(
                output=output_value,
                content=content,
                model=self._model,
                chunk=chunk,
                is_final=hasattr(chunk, "_is_final") and chunk._is_final,
            )
        else:
            # Handle LiteLLM streaming (ChatCompletionChunk)
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                content = None
                if hasattr(choice, "delta") and choice.delta:
                    content = getattr(choice.delta, "content", None)

                if content is not None:
                    self._full_content += content

                return LanguageModelResponseChunk(
                    content=content,
                    output=self._full_content,
                    model=getattr(chunk, "model", self._model),
                    finish_reason=getattr(choice, "finish_reason", None),
                    chunk=chunk,
                    is_final=getattr(choice, "finish_reason", None) is not None,
                )
        return None

    def collect(self) -> LanguageModelResponse[T]:
        """Collect all chunks and return a complete LanguageModelResponse object (sync mode)."""
        if self._is_async:
            raise RuntimeError(
                "Cannot use sync collect() on async stream. Use async collect() instead."
            )

        if not self._chunks:
            # Consume the stream if not already consumed
            list(self)

        return self._build_response()

    async def async_collect(self) -> LanguageModelResponse[T]:
        """Collect all chunks and return a complete LanguageModelResponse object (async mode)."""
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async collect() on sync stream. Use sync collect() instead."
            )

        if not self._chunks:
            # Consume the stream if not already consumed
            async for _ in self:
                pass

        return self._build_response()

    def _build_response(self) -> LanguageModelResponse[T]:
        """Build the final LanguageModelResponse from collected chunks."""
        if self._is_instructor and self._chunks:
            # For instructor, the final chunk contains the complete object
            final_chunk = self._chunks[-1]

            # Check if stream collector is available for raw content
            raw_content = None
            raw_completion = None
            tool_calls = None

            if hasattr(self._stream, "collector"):
                collector = self._stream.collector
                raw_content = collector.get_raw_content()
                raw_completion = collector.get_raw_completion()
                tool_calls = collector.get_tool_calls()
            elif hasattr(self._stream, "get_raw_content"):
                raw_content = self._stream.get_raw_content()
                raw_completion = (
                    self._stream.get_raw_completion()
                    if hasattr(self._stream, "get_raw_completion")
                    else None
                )
                tool_calls = (
                    self._stream.get_tool_calls()
                    if hasattr(self._stream, "get_tool_calls")
                    else None
                )

            return LanguageModelResponse(
                output=final_chunk.output,
                model=final_chunk.model or self._model or "unknown",
                completion=raw_completion,
                content=raw_content,
                tool_calls=tool_calls,
            )
        else:
            # For LiteLLM, combine content from all chunks
            content_parts = [chunk.content for chunk in self._chunks if chunk.content]
            combined_content = "".join(content_parts)

            # Create a mock completion for consistency
            mock_completion = None
            if self._chunks:
                mock_completion = self._chunks[-1].chunk

            return LanguageModelResponse(
                output=combined_content,
                model=self._model or "unknown",
                completion=mock_completion,
                content=combined_content,
            )

    def to_response(self) -> LanguageModelResponse[T]:
        """Convert the stream to a LanguageModelResponse object (sync mode).

        This method can only be called after the stream has been fully consumed.
        It's an alias for collect() with a check for consumption state.

        Returns:
            LanguageModelResponse[T]: The complete response object

        Raises:
            RuntimeError: If the stream has not been fully consumed or is async
        """
        if self._is_async:
            raise RuntimeError(
                "Cannot use sync to_response() on async stream. Use async to_response() instead."
            )

        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to response. "
                "Use collect() or iterate through the stream first."
            )

        return self.collect()

    async def async_to_response(self) -> LanguageModelResponse[T]:
        """Convert the stream to a LanguageModelResponse object (async mode).

        This method can only be called after the stream has been fully consumed.
        It's an alias for async_collect() with a check for consumption state.

        Returns:
            LanguageModelResponse[T]: The complete response object

        Raises:
            RuntimeError: If the stream has not been fully consumed or is sync
        """
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async to_response() on sync stream. Use sync to_response() instead."
            )

        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to response. "
                "Use async_collect() or iterate through the stream first."
            )

        return await self.async_collect()

    def to_message(self) -> Any:
        """Convert the stream to a ChatCompletionMessageParam (sync mode).

        This method can only be called after the stream has been fully consumed.
        It converts the final response to a message format.

        Returns:
            ChatCompletionMessageParam: The response as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed or is async
        """
        if self._is_async:
            raise RuntimeError(
                "Cannot use sync to_message() on async stream. Use async to_message() instead."
            )

        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. "
                "Use collect() or iterate through the stream first."
            )

        response = self.collect()
        return response.to_message()

    async def async_to_message(self) -> Any:
        """Convert the stream to a ChatCompletionMessageParam (async mode).

        This method can only be called after the stream has been fully consumed.
        It converts the final response to a message format.

        Returns:
            ChatCompletionMessageParam: The response as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed or is sync
        """
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async to_message() on sync stream. Use sync to_message() instead."
            )

        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. "
                "Use async_collect() or iterate through the stream first."
            )

        response = await self.async_collect()
        return response.to_message()
