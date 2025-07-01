"""hammad.ai.completions.types

Contains types for working with language model completions."""

import json
from typing import (
    Any,
    Dict,
    List,
    Generic,
    TypeVar,
    TypeAlias,
    Literal,
    Optional,
    Union,
    Type,
    Iterator,
    AsyncIterator,
)

from pydantic import BaseModel, ConfigDict

try:
    from openai.types.chat import (
        ChatCompletionMessageParam,
        ChatCompletionMessageToolCall,
    )
except ImportError:
    raise ImportError(
        "Using the `hammad.ai.completions` extension requires the `openai` package to be installed.\n"
        "Please either install the `openai` package, or install the `hammad.ai` extension with:\n"
        "`pip install 'hammad-python[ai]'"
    )


__all__ = (
    "Completion",
    "CompletionsInputParam",
    "CompletionsOutputType",
    "CompletionsInstructorModeParam",
    "CompletionChunk",
    "CompletionStream",
    "AsyncCompletionStream",
)


CompletionsInputParam = Union[
    str, ChatCompletionMessageParam, List[ChatCompletionMessageParam], Any
]
"""Type alias for the input parameters of a completion."""


CompletionsOutputType = TypeVar("CompletionsOutputType")
"""Type variable for the output type of a completion."""


CompletionsModelName: TypeAlias = Literal[
    "anthropic/claude-3-7-sonnet-latest",
    "anthropic/claude-3-5-haiku-latest",
    "anthropic/claude-3-5-sonnet-latest",
    "anthropic/claude-3-opus-latest",
    "claude-3-7-sonnet-latest",
    "claude-3-5-haiku-latest",
    "bedrock/amazon.titan-tg1-large",
    "bedrock/amazon.titan-text-lite-v1",
    "bedrock/amazon.titan-text-express-v1",
    "bedrock/us.amazon.nova-pro-v1:0",
    "bedrock/us.amazon.nova-lite-v1:0",
    "bedrock/us.amazon.nova-micro-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "bedrock/anthropic.claude-instant-v1",
    "bedrock/anthropic.claude-v2:1",
    "bedrock/anthropic.claude-v2",
    "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/us.anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock/cohere.command-text-v14",
    "bedrock/cohere.command-r-v1:0",
    "bedrock/cohere.command-r-plus-v1:0",
    "bedrock/cohere.command-light-text-v14",
    "bedrock/meta.llama3-8b-instruct-v1:0",
    "bedrock/meta.llama3-70b-instruct-v1:0",
    "bedrock/meta.llama3-1-8b-instruct-v1:0",
    "bedrock/us.meta.llama3-1-8b-instruct-v1:0",
    "bedrock/meta.llama3-1-70b-instruct-v1:0",
    "bedrock/us.meta.llama3-1-70b-instruct-v1:0",
    "bedrock/meta.llama3-1-405b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-11b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-90b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-1b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-3b-instruct-v1:0",
    "bedrock/us.meta.llama3-3-70b-instruct-v1:0",
    "bedrock/mistral.mistral-7b-instruct-v0:2",
    "bedrock/mistral.mixtral-8x7b-instruct-v0:1",
    "bedrock/mistral.mistral-large-2402-v1:0",
    "bedrock/mistral.mistral-large-2407-v1:0",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-latest",
    "cohere/c4ai-aya-expanse-32b",
    "cohere/c4ai-aya-expanse-8b",
    "cohere/command",
    "cohere/command-light",
    "cohere/command-light-nightly",
    "cohere/command-nightly",
    "cohere/command-r",
    "cohere/command-r-03-2024",
    "cohere/command-r-08-2024",
    "cohere/command-r-plus",
    "cohere/command-r-plus-04-2024",
    "cohere/command-r-plus-08-2024",
    "cohere/command-r7b-12-2024",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
    "google-gla/gemini-1.0-pro",
    "google-gla/gemini-1.5-flash",
    "google-gla/gemini-1.5-flash-8b",
    "google-gla/gemini-1.5-pro",
    "google-gla/gemini-2.0-flash-exp",
    "google-gla/gemini-2.0-flash-thinking-exp-01-21",
    "google-gla/gemini-exp-1206",
    "google-gla/gemini-2.0-flash",
    "google-gla/gemini-2.0-flash-lite-preview-02-05",
    "google-gla/gemini-2.0-pro-exp-02-05",
    "google-gla/gemini-2.5-flash-preview-04-17",
    "google-gla/gemini-2.5-pro-exp-03-25",
    "google-gla/gemini-2.5-pro-preview-03-25",
    "google-vertex/gemini-1.0-pro",
    "google-vertex/gemini-1.5-flash",
    "google-vertex/gemini-1.5-flash-8b",
    "google-vertex/gemini-1.5-pro",
    "google-vertex/gemini-2.0-flash-exp",
    "google-vertex/gemini-2.0-flash-thinking-exp-01-21",
    "google-vertex/gemini-exp-1206",
    "google-vertex/gemini-2.0-flash",
    "google-vertex/gemini-2.0-flash-lite-preview-02-05",
    "google-vertex/gemini-2.0-pro-exp-02-05",
    "google-vertex/gemini-2.5-flash-preview-04-17",
    "google-vertex/gemini-2.5-pro-exp-03-25",
    "google-vertex/gemini-2.5-pro-preview-03-25",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0125-preview",
    "gpt-4-0314",
    "gpt-4-0613",
    "gpt-4-1106-preview",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-4-32k-0613",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-turbo-preview",
    "gpt-4-vision-preview",
    "gpt-4.1",
    "gpt-4.1-2025-04-14",
    "gpt-4.1-mini",
    "gpt-4.1-mini-2025-04-14",
    "gpt-4.1-nano",
    "gpt-4.1-nano-2025-04-14",
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-11-20",
    "gpt-4o-audio-preview",
    "gpt-4o-audio-preview-2024-10-01",
    "gpt-4o-audio-preview-2024-12-17",
    "gpt-4o-mini",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-mini-audio-preview",
    "gpt-4o-mini-audio-preview-2024-12-17",
    "gpt-4o-mini-search-preview",
    "gpt-4o-mini-search-preview-2025-03-11",
    "gpt-4o-search-preview",
    "gpt-4o-search-preview-2025-03-11",
    "groq/distil-whisper-large-v3-en",
    "groq/gemma2-9b-it",
    "groq/llama-3.3-70b-versatile",
    "groq/llama-3.1-8b-instant",
    "groq/llama-guard-3-8b",
    "groq/llama3-70b-8192",
    "groq/llama3-8b-8192",
    "groq/whisper-large-v3",
    "groq/whisper-large-v3-turbo",
    "groq/playai-tts",
    "groq/playai-tts-arabic",
    "groq/qwen-qwq-32b",
    "groq/mistral-saba-24b",
    "groq/qwen-2.5-coder-32b",
    "groq/qwen-2.5-32b",
    "groq/deepseek-r1-distill-qwen-32b",
    "groq/deepseek-r1-distill-llama-70b",
    "groq/llama-3.3-70b-specdec",
    "groq/llama-3.2-1b-preview",
    "groq/llama-3.2-3b-preview",
    "groq/llama-3.2-11b-vision-preview",
    "groq/llama-3.2-90b-vision-preview",
    "mistral/codestral-latest",
    "mistral/mistral-large-latest",
    "mistral/mistral-moderation-latest",
    "mistral/mistral-small-latest",
    "o1",
    "o1-2024-12-17",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1-preview",
    "o1-preview-2024-09-12",
    "o3",
    "o3-2025-04-16",
    "o3-mini",
    "o3-mini-2025-01-31",
    "openai/chatgpt-4o-latest",
    "openai/gpt-3.5-turbo",
    "openai/gpt-3.5-turbo-0125",
    "openai/gpt-3.5-turbo-0301",
    "openai/gpt-3.5-turbo-0613",
    "openai/gpt-3.5-turbo-1106",
    "openai/gpt-3.5-turbo-16k",
    "openai/gpt-3.5-turbo-16k-0613",
    "openai/gpt-4",
    "openai/gpt-4-0125-preview",
    "openai/gpt-4-0314",
    "openai/gpt-4-0613",
    "openai/gpt-4-1106-preview",
    "openai/gpt-4-32k",
    "openai/gpt-4-32k-0314",
    "openai/gpt-4-32k-0613",
    "openai/gpt-4-turbo",
    "openai/gpt-4-turbo-2024-04-09",
    "openai/gpt-4-turbo-preview",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4.1",
    "openai/gpt-4.1-2025-04-14",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1-mini-2025-04-14",
    "openai/gpt-4.1-nano",
    "openai/gpt-4.1-nano-2025-04-14",
    "openai/gpt-4o",
    "openai/gpt-4o-2024-05-13",
    "openai/gpt-4o-2024-08-06",
    "openai/gpt-4o-2024-11-20",
    "openai/gpt-4o-audio-preview",
    "openai/gpt-4o-audio-preview-2024-10-01",
    "openai/gpt-4o-audio-preview-2024-12-17",
    "openai/gpt-4o-mini",
    "openai/gpt-4o-mini-2024-07-18",
    "openai/gpt-4o-mini-audio-preview",
    "openai/gpt-4o-mini-audio-preview-2024-12-17",
    "openai/gpt-4o-mini-search-preview",
    "openai/gpt-4o-mini-search-preview-2025-03-11",
    "openai/gpt-4o-search-preview",
    "openai/gpt-4o-search-preview-2025-03-11",
    "openai/o1",
    "openai/o1-2024-12-17",
    "openai/o1-mini",
    "openai/o1-mini-2024-09-12",
    "openai/o1-preview",
    "openai/o1-preview-2024-09-12",
    "openai/o3",
    "openai/o3-2025-04-16",
    "openai/o3-mini",
    "openai/o3-mini-2025-01-31",
    "openai/o4-mini",
    "openai/o4-mini-2025-04-16",
    "xai/grok-3-latest",
]
"""Helper alias for various compatible models usable with litellm
completions."""


CompletionsInstructorModeParam = Literal[
    "function_call",
    "parallel_tool_call",
    "tool_call",
    "tools_strict",
    "json_mode",
    "json_o1",
    "markdown_json_mode",
    "json_schema_mode",
    "anthropic_tools",
    "anthropic_reasoning_tools",
    "anthropic_json",
    "mistral_tools",
    "mistral_structured_outputs",
    "vertexai_tools",
    "vertexai_json",
    "vertexai_parallel_tools",
    "gemini_json",
    "gemini_tools",
    "genai_tools",
    "genai_structured_outputs",
    "cohere_tools",
    "cohere_json_object",
    "cerebras_tools",
    "cerebras_json",
    "fireworks_tools",
    "fireworks_json",
    "writer_tools",
    "bedrock_tools",
    "bedrock_json",
    "perplexity_json",
    "openrouter_structured_outputs",
]
"""Instructor prompt/parsing mode for structured outputs."""


class Completion(BaseModel, Generic[CompletionsOutputType]):
    """Extended response object for completions and structured outputs
    generated by language models using the `completions` resource
    within the `hammad.ai` extension."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    output: CompletionsOutputType
    """The output content of the completion. This is in the type that was
    requested within the `type` parameter."""

    model: str
    """The model that was used to generate the completion."""

    content: str | None = None
    """The actual response content of the completion. This is the string that
    was generated by the model."""

    tool_calls: ChatCompletionMessageToolCall | Any | None = None
    """The tool calls that were made by the model. This is a list of tool calls
    that were made by the model."""

    refusal: str | None = None
    """The refusal message generated by the model. This is the string that
    was generated by the model when it refused to generate the completion."""

    completion: Any | None = None
    """The original completion object in the OpenAI Chat Compeltions specification,
    generated by the model."""

    def has_tool_calls(self, tools: str | List[str] | None = None) -> bool:
        """Checks whether the completion has tool calls in general,
        or if the tool calls are for a specific tool.

        Args:
            tools : The tool(s) to check for. If None, checks for any tool calls.

        Returns:
            bool : True if the completion has tool calls, False otherwise.
        """
        if self.tool_calls is None:
            return False
        if tools is None and self.tool_calls is not None:
            return True

        if tools:
            if not isinstance(tools, list):
                tools = [tools]
            return any(
                tool_call.function.name in tools for tool_call in self.tool_calls
            )
        return False

    def get_tool_call_parameters(
        self, tool: str | None = None
    ) -> Dict[str, Any] | None:
        """Returns the generated parameters for a tool
        call within a completion. If the completion has multiple tool calls,
        and no tool is specified, an error will be raised.

        Args:
            tool : The name of the tool to get the parameters for.

        Returns:
            Dict[str, Any] : The generated parameters for the tool call.
        """
        if self.tool_calls is None:
            return None

        if tool is None:
            if len(self.tool_calls) > 1:
                raise ValueError(
                    "Multiple tool calls found in completion, and no tool specified."
                )
            tool = self.tool_calls[0].function.name

        for tool_call in self.tool_calls:
            if tool_call.function.name == tool:
                return json.loads(tool_call.function.arguments)
        return None

    def to_message(self) -> ChatCompletionMessageParam:
        """Convert the completion to a ChatCompletionMessageParam.

        This method converts the completion into a message that can be used
        in subsequent chat completion calls. It handles different output types
        appropriately.

        Returns:
            ChatCompletionMessageParam: The completion as a chat message
        """
        if self.tool_calls:
            # If there are tool calls, return assistant message with tool calls
            return {
                "role": "assistant",
                "content": self.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in self.tool_calls
                ],
            }
        elif self.refusal:
            # If there's a refusal, return assistant message with refusal
            return {"role": "assistant", "refusal": self.refusal}
        else:
            # Standard assistant response
            content = self.content
            if content is None and self.output != self.content:
                # For structured outputs, convert to string if needed
                if hasattr(self.output, "model_dump_json"):
                    content = self.output.model_dump_json()
                elif hasattr(self.output, "__dict__"):
                    content = json.dumps(self.output.__dict__)
                else:
                    content = str(self.output)

            return {"role": "assistant", "content": content or str(self.output)}

    def __str__(self) -> str:
        """Pretty prints the completion object."""
        output = "Completion:"

        if self.output or self.content:
            output += f"\n{self.output if self.output else self.content}"
        else:
            output += f"\n{self.completion}"

        output += f"\n\n>>> Model: {self.model}"
        output += f"\n>>> Tool Calls: {len(self.tool_calls) if self.tool_calls else 0}"

        return output


class CompletionChunk(BaseModel, Generic[CompletionsOutputType]):
    """Represents a chunk of data from a completion stream.

    This class unifies chunks from both LiteLLM and Instructor streaming,
    providing a consistent interface for processing streaming completions.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: str | None = None
    """The content delta for this chunk."""

    output: CompletionsOutputType | None = None
    """The structured output for this chunk (from instructor)."""

    model: str | None = None
    """The model that generated this chunk."""

    finish_reason: str | None = None
    """The reason the stream finished (if applicable)."""

    chunk: Any | None = None
    """The original chunk object from the provider."""

    is_final: bool = False
    """Whether this is the final chunk in the stream."""

    def __bool__(self) -> bool:
        """Check if this chunk has meaningful content."""
        return bool(self.content or self.output or self.finish_reason)


class CompletionStream(Generic[CompletionsOutputType]):
    """Synchronous stream wrapper for completion streaming.

    This class provides a unified interface for streaming completions
    from both LiteLLM and Instructor, handling the different chunk
    formats and providing consistent access patterns.
    """

    def __init__(
        self,
        stream: Iterator[Any],
        output_type: Type[CompletionsOutputType] = str,
        model: str | None = None,
    ):
        self._stream = stream
        self._output_type = output_type
        self._model = model
        self._chunks: List[CompletionChunk] = []
        self._final_output: CompletionsOutputType | None = None
        self._is_instructor = output_type != str
        self._is_consumed = False

    def __iter__(self) -> Iterator[CompletionChunk]:
        """Iterate over completion chunks."""
        for chunk in self._stream:
            completion_chunk = self._process_chunk(chunk)
            if completion_chunk:
                self._chunks.append(completion_chunk)
                yield completion_chunk
        self._is_consumed = True

    def _process_chunk(self, chunk: Any) -> CompletionChunk | None:
        """Process a raw chunk into a CompletionChunk."""
        if self._is_instructor:
            # Handle instructor streaming (Partial/Iterable)
            # Extract .value if it exists (for converted non-Pydantic types)
            output = chunk
            if hasattr(chunk, "value"):
                output = chunk.value

            return CompletionChunk(
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

                return CompletionChunk(
                    content=content,
                    model=getattr(chunk, "model", self._model),
                    finish_reason=getattr(choice, "finish_reason", None),
                    chunk=chunk,
                    is_final=getattr(choice, "finish_reason", None) is not None,
                )
        return None

    def collect(self) -> Completion[CompletionsOutputType]:
        """Collect all chunks and return a complete Completion object."""
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

            return Completion(
                output=final_chunk.output,
                model=final_chunk.model or self._model or "unknown",
                content=raw_content,
                tool_calls=tool_calls,
                completion=raw_completion,
            )
        else:
            # For LiteLLM, combine content from all chunks
            content_parts = [chunk.content for chunk in self._chunks if chunk.content]
            combined_content = "".join(content_parts)

            return Completion(
                output=combined_content,
                model=self._model or "unknown",
                content=combined_content,
                completion=None,  # Don't set mock chunks as completion
            )

    def to_completion(self) -> Completion[CompletionsOutputType]:
        """Convert the stream to a Completion object.

        This method can only be called after the stream has been fully consumed.
        It's an alias for collect() with a check for consumption state.

        Returns:
            Completion[CompletionsOutputType]: The complete completion object

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to completion. Use collect() or iterate through the stream first."
            )

        return self.collect()

    def to_message(self) -> ChatCompletionMessageParam:
        """Convert the stream to a ChatCompletionMessageParam.

        This method can only be called after the stream has been fully consumed.
        It converts the final completion to a message format.

        Returns:
            ChatCompletionMessageParam: The completion as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. Use collect() or iterate through the stream first."
            )

        completion = self.collect()
        return completion.to_message()


class AsyncCompletionStream(Generic[CompletionsOutputType]):
    """Asynchronous stream wrapper for completion streaming.

    This class provides a unified interface for async streaming completions
    from both LiteLLM and Instructor, handling the different chunk
    formats and providing consistent access patterns.
    """

    def __init__(
        self,
        stream: AsyncIterator[Any],
        output_type: Type[CompletionsOutputType] = str,
        model: str | None = None,
    ):
        self._stream = stream
        self._output_type = output_type
        self._model = model
        self._chunks: List[CompletionChunk] = []
        self._final_output: CompletionsOutputType | None = None
        self._is_instructor = output_type != str
        self._is_consumed = False

    def __aiter__(self) -> AsyncIterator[CompletionChunk]:
        """Async iterate over completion chunks."""
        return self

    async def __anext__(self) -> CompletionChunk:
        """Get the next completion chunk."""
        try:
            chunk = await self._stream.__anext__()
            completion_chunk = self._process_chunk(chunk)
            if completion_chunk:
                self._chunks.append(completion_chunk)
                return completion_chunk
            else:
                return await self.__anext__()  # Skip empty chunks
        except StopAsyncIteration:
            self._is_consumed = True
            raise StopAsyncIteration

    def _process_chunk(self, chunk: Any) -> CompletionChunk | None:
        """Process a raw chunk into a CompletionChunk."""
        if self._is_instructor:
            # Handle instructor streaming (Partial/Iterable)
            # Extract .value if it exists (for converted non-Pydantic types)
            output = chunk
            if hasattr(chunk, "value"):
                output = chunk.value

            return CompletionChunk(
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

                return CompletionChunk(
                    content=content,
                    model=getattr(chunk, "model", self._model),
                    finish_reason=getattr(choice, "finish_reason", None),
                    chunk=chunk,
                    is_final=getattr(choice, "finish_reason", None) is not None,
                )
        return None

    async def collect(self) -> Completion[CompletionsOutputType]:
        """Collect all chunks and return a complete Completion object."""
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

            return Completion(
                output=final_chunk.output,
                model=final_chunk.model or self._model or "unknown",
                content=raw_content,
                tool_calls=tool_calls,
                completion=raw_completion,
            )
        else:
            # For LiteLLM, combine content from all chunks
            content_parts = [chunk.content for chunk in self._chunks if chunk.content]
            combined_content = "".join(content_parts)

            return Completion(
                output=combined_content,
                model=self._model or "unknown",
                content=combined_content,
                completion=None,  # Don't set mock chunks as completion
            )

    async def to_completion(self) -> Completion[CompletionsOutputType]:
        """Convert the stream to a Completion object.

        This method can only be called after the stream has been fully consumed.
        It's an alias for collect() with a check for consumption state.

        Returns:
            Completion[CompletionsOutputType]: The complete completion object

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to completion. Use collect() or iterate through the stream first."
            )

        return await self.collect()

    async def to_message(self) -> ChatCompletionMessageParam:
        """Convert the stream to a ChatCompletionMessageParam.

        This method can only be called after the stream has been fully consumed.
        It converts the final completion to a message format.

        Returns:
            ChatCompletionMessageParam: The completion as a chat message

        Raises:
            RuntimeError: If the stream has not been fully consumed
        """
        if not self._is_consumed and not self._chunks:
            raise RuntimeError(
                "Stream must be fully consumed before converting to message. Use collect() or iterate through the stream first."
            )

        completion = await self.collect()
        return completion.to_message()
