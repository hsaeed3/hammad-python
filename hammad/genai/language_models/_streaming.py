"""hammad.genai.language_models._streaming"""

from typing import (
    List,
    Type,
    TypeVar,
    Generic,
    Iterator,
    AsyncIterator,
    Optional,
    Any,
)

from .language_model_response import LanguageModelResponse
from .language_model_response_chunk import LanguageModelResponseChunk

__all__ = [
    "Stream",
    "AsyncStream",
]

T = TypeVar("T")


class Stream(Generic[T]):
    """Synchronous stream wrapper for language model streaming.

    This class provides a unified interface for streaming responses
    from both LiteLLM and Instructor, handling the different chunk
    formats and providing consistent access patterns.
    """

    def __init__(
        self,
        stream: Iterator[Any],
        output_type: Type[T] = str,
        model: Optional[str] = None,
    ):
        """Initialize the stream.
        
        Args:
            stream: The underlying stream iterator
            output_type: The expected output type
            model: The model name
        """
        self._stream = stream
        self._output_type = output_type
        self._model = model
        self._chunks: List[LanguageModelResponseChunk[T]] = []
        self._final_output: Optional[T] = None
        self._is_instructor = output_type != str
        self._is_consumed = False

    def __iter__(self) -> Iterator[LanguageModelResponseChunk[T]]:
        """Iterate over response chunks."""
        for chunk in self._stream:
            response_chunk = self._process_chunk(chunk)
            if response_chunk:
                self._chunks.append(response_chunk)
                yield response_chunk
        self._is_consumed = True

    def _process_chunk(self, chunk: Any) -> Optional[LanguageModelResponseChunk[T]]:
        """Process a raw chunk into a LanguageModelResponseChunk."""
        if self._is_instructor:
            # Handle instructor streaming (Partial/Iterable)
            # Extract .value if it exists (for converted non-Pydantic types)
            output = chunk
            if hasattr(chunk, "value"):
                output = chunk.value
            # For primitive types like int, extract the actual value
            elif hasattr(chunk, "content") and self._output_type in (int, float, bool, str):
                output = chunk.content
            elif self._output_type in (int, float, bool) and hasattr(chunk, "__dict__"):
                # Try to extract the first field value for primitive types
                chunk_dict = chunk.__dict__
                if len(chunk_dict) == 1:
                    output = next(iter(chunk_dict.values()))

            return LanguageModelResponseChunk(
                output=output,
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

                return LanguageModelResponseChunk(
                    content=content,
                    model=getattr(chunk, "model", self._model),
                    finish_reason=getattr(choice, "finish_reason", None),
                    chunk=chunk,
                    is_final=getattr(choice, "finish_reason", None) is not None,
                )
        return None

    def collect(self) -> LanguageModelResponse[T]:
        """Collect all chunks and return a complete LanguageModelResponse object."""
        if not self._chunks:
            # Consume the stream if not already consumed
            list(self)

        if self._is_instructor and self._chunks:
            # For instructor, the final chunk contains the complete object
            # The output is already extracted (.value) in _process_chunk if needed
            final_chunk = self._chunks[-1]

            # Check if stream is from wrapper to get raw content
            raw_content = None
            raw_completion = None
            if hasattr(self._stream, "get_raw_content"):
                raw_content = self._stream.get_raw_content()
            if hasattr(self._stream, "get_raw_completion"):
                raw_completion = self._stream.get_raw_completion()

            # Check for tool calls from wrapper
            tool_calls = None
            if hasattr(self._stream, "get_tool_calls"):
                tool_calls = self._stream.get_tool_calls()

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
        """Convert the stream to a LanguageModelResponse object.

        This method can only be called after the stream has been fully consumed.
        It's an alias for collect() with a check for consumption state.

        Returns:
            LanguageModelResponse[T]: The complete response object

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to response. "
                "Use collect() or iterate through the stream first."
            )

        return self.collect()

    def to_message(self) -> Any:
        """Convert the stream to a ChatCompletionMessageParam.

        This method can only be called after the stream has been fully consumed.
        It converts the final response to a message format.

        Returns:
            ChatCompletionMessageParam: The response as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. "
                "Use collect() or iterate through the stream first."
            )

        response = self.collect()
        return response.to_message()


class AsyncStream(Generic[T]):
    """Asynchronous stream wrapper for language model streaming.

    This class provides a unified interface for async streaming responses
    from both LiteLLM and Instructor, handling the different chunk
    formats and providing consistent access patterns.
    """

    def __init__(
        self,
        stream: AsyncIterator[Any],
        output_type: Type[T] = str,
        model: Optional[str] = None,
    ):
        """Initialize the async stream.
        
        Args:
            stream: The underlying async stream iterator
            output_type: The expected output type
            model: The model name
        """
        self._stream = stream
        self._output_type = output_type
        self._model = model
        self._chunks: List[LanguageModelResponseChunk[T]] = []
        self._final_output: Optional[T] = None
        self._is_instructor = output_type != str
        self._is_consumed = False

    def __aiter__(self) -> AsyncIterator[LanguageModelResponseChunk[T]]:
        """Async iterate over response chunks."""
        return self

    async def __anext__(self) -> LanguageModelResponseChunk[T]:
        """Get the next response chunk."""
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
            # Extract .value if it exists (for converted non-Pydantic types)
            output = chunk
            if hasattr(chunk, "value"):
                output = chunk.value
            # For primitive types like int, extract the actual value
            elif hasattr(chunk, "content") and self._output_type in (int, float, bool, str):
                output = chunk.content
            elif self._output_type in (int, float, bool) and hasattr(chunk, "__dict__"):
                # Try to extract the first field value for primitive types
                chunk_dict = chunk.__dict__
                if len(chunk_dict) == 1:
                    output = next(iter(chunk_dict.values()))

            return LanguageModelResponseChunk(
                output=output,
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

                return LanguageModelResponseChunk(
                    content=content,
                    model=getattr(chunk, "model", self._model),
                    finish_reason=getattr(choice, "finish_reason", None),
                    chunk=chunk,
                    is_final=getattr(choice, "finish_reason", None) is not None,
                )
        return None

    async def collect(self) -> LanguageModelResponse[T]:
        """Collect all chunks and return a complete LanguageModelResponse object."""
        if not self._chunks:
            # Consume the stream if not already consumed
            async for _ in self:
                pass

        if self._is_instructor and self._chunks:
            # For instructor, the final chunk contains the complete object
            # The output is already extracted (.value) in _process_chunk if needed
            final_chunk = self._chunks[-1]

            # Check if stream is from wrapper to get raw content
            raw_content = None
            raw_completion = None
            if hasattr(self._stream, "get_raw_content"):
                raw_content = self._stream.get_raw_content()
            if hasattr(self._stream, "get_raw_completion"):
                raw_completion = self._stream.get_raw_completion()

            # Check for tool calls from wrapper
            tool_calls = None
            if hasattr(self._stream, "get_tool_calls"):
                tool_calls = self._stream.get_tool_calls()

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

    async def to_response(self) -> LanguageModelResponse[T]:
        """Convert the stream to a LanguageModelResponse object.

        This method can only be called after the stream has been fully consumed.
        It's an alias for collect() with a check for consumption state.

        Returns:
            LanguageModelResponse[T]: The complete response object

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to response. "
                "Use collect() or iterate through the stream first."
            )

        return await self.collect()

    async def to_message(self) -> Any:
        """Convert the stream to a ChatCompletionMessageParam.

        This method can only be called after the stream has been fully consumed.
        It converts the final response to a message format.

        Returns:
            ChatCompletionMessageParam: The response as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. "
                "Use collect() or iterate through the stream first."
            )

        response = await self.collect()
        return response.to_message()