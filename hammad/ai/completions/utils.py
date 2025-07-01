"""hammad.ai.completions.utils"""

import json
from typing import (
    Optional,
    List,
    Iterator,
    AsyncIterator,
    TypeVar,
    Type,
    Any,
)

try:
    from pydantic import BaseModel
except ImportError:
    raise ImportError(
        "Using completion stream parsing requires the `openai` and `instructor` packages."
        "Please install with: pip install 'hammad-python[ai]'"
    )

from ...cache import cached
from .types import (
    CompletionsInputParam,
    ChatCompletionMessageParam,
    CompletionStream,
    AsyncCompletionStream,
    Completion,
)

T = TypeVar("T", bound=BaseModel)

__all__ = (
    "parse_completions_input",
    "create_completion_stream",
    "create_async_completion_stream",
    "format_tool_calls",
    "convert_response_to_completion",
    "InstructorStreamWrapper",
    "AsyncInstructorStreamWrapper",
)


@cached
def parse_completions_input(
    input: CompletionsInputParam,
    instructions: Optional[str] = None,
) -> List[ChatCompletionMessageParam]:
    """Parse various input formats into a list of ChatCompletionMessageParam.

    This function handles:
    - Plain strings (converted to user messages)
    - Strings with message blocks like [system], [user], [assistant]
    - Single ChatCompletionMessageParam objects
    - Lists of ChatCompletionMessageParam objects
    - Objects with model_dump() method

    Args:
        input: The input to parse
        instructions: Optional system instructions to prepend

    Returns:
        List of ChatCompletionMessageParam objects
    """
    messages: List[ChatCompletionMessageParam] = []

    # Handle string inputs
    if isinstance(input, str):
        # Check if string contains message blocks like [system], [user], [assistant]
        import re

        # Pattern to match only allowed message blocks (system, user, assistant)
        pattern = (
            r"\[(system|user|assistant)\]\s*(.*?)(?=\[(?:system|user|assistant)\]|$)"
        )
        matches = re.findall(pattern, input, re.DOTALL | re.IGNORECASE)

        if matches:
            # Validate that we only have allowed roles
            allowed_roles = {"system", "user", "assistant"}
            found_roles = {role.lower() for role, _ in matches}

            if not found_roles.issubset(allowed_roles):
                invalid_roles = found_roles - allowed_roles
                raise ValueError(
                    f"Invalid message roles found: {invalid_roles}. Only 'system', 'user', and 'assistant' are allowed."
                )

            # Parse message blocks
            system_contents = []

            for role, content in matches:
                content = content.strip()
                if content:
                    if role.lower() == "system":
                        system_contents.append(content)
                    else:
                        messages.append({"role": role.lower(), "content": content})

            # Combine system contents if any exist
            if system_contents:
                combined_system = "\n\n".join(system_contents)
                if instructions:
                    combined_system = f"{combined_system}\n\n{instructions}"
                messages.insert(0, {"role": "system", "content": combined_system})
            elif instructions:
                messages.insert(0, {"role": "system", "content": instructions})
        else:
            # Plain string - create user message
            if instructions:
                messages.append({"role": "system", "content": instructions})
            messages.append({"role": "user", "content": input})

    # Handle single message object
    elif hasattr(input, "model_dump"):
        message_dict = input.model_dump()
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.append(message_dict)

    # Handle list of messages
    elif isinstance(input, list):
        system_contents = []
        other_messages = []

        for item in input:
            if hasattr(item, "model_dump"):
                msg_dict = item.model_dump()
            else:
                msg_dict = item

            if msg_dict.get("role") == "system":
                system_contents.append(msg_dict.get("content", ""))
            else:
                other_messages.append(msg_dict)

        # Combine system messages and instructions
        if system_contents or instructions:
            combined_system_parts = []
            if system_contents:
                combined_system_parts.extend(system_contents)
            if instructions:
                combined_system_parts.append(instructions)

            messages.append(
                {"role": "system", "content": "\n\n".join(combined_system_parts)}
            )

        messages.extend(other_messages)

    # Handle single dictionary or other object
    else:
        if hasattr(input, "model_dump"):
            message_dict = input.model_dump()
        else:
            message_dict = input

        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.append(message_dict)

    return messages


def create_completion_stream(
    stream: Iterator[Any], output_type: Type[T] = str, model: str | None = None
) -> CompletionStream[T]:
    """Create a unified completion stream from a raw stream.

    This function wraps raw streams from both LiteLLM and Instructor
    into a unified CompletionStream interface. It automatically detects
    the stream type based on the output_type parameter.

    Args:
        stream: The raw stream from LiteLLM or Instructor
        output_type: The expected output type (str for LiteLLM, model class for Instructor)
        model: The model name for metadata

    Returns:
        CompletionStream: Unified stream interface

    Examples:
        # For LiteLLM string completions
        litellm_stream = litellm.completion(model="gpt-4", messages=messages, stream=True)
        unified_stream = create_completion_stream(litellm_stream, str, "gpt-4")

        # For Instructor structured outputs
        instructor_stream = instructor_client.completion(response_model=User, messages=messages, stream=True)
        unified_stream = create_completion_stream(instructor_stream, User, "gpt-4")
    """
    return CompletionStream(stream, output_type, model)


def create_async_completion_stream(
    stream: AsyncIterator[Any], output_type: Type[T] = str, model: str | None = None
) -> AsyncCompletionStream[T]:
    """Create a unified async completion stream from a raw async stream.

    This function wraps raw async streams from both LiteLLM and Instructor
    into a unified AsyncCompletionStream interface. It automatically detects
    the stream type based on the output_type parameter.

    Args:
        stream: The raw async stream from LiteLLM or Instructor
        output_type: The expected output type (str for LiteLLM, model class for Instructor)
        model: The model name for metadata

    Returns:
        AsyncCompletionStream: Unified async stream interface

    Examples:
        ```python
        # For LiteLLM async string completions
        litellm_stream = await litellm.acompletion(model="gpt-4", messages=messages, stream=True)
        unified_stream = create_async_completion_stream(litellm_stream, str, "gpt-4")

        # For Instructor async structured outputs
        instructor_stream = await instructor_client.acompletion(response_model=User, messages=messages, stream=True)
        unified_stream = create_async_completion_stream(instructor_stream, User, "gpt-4")
        ```
    """
    return AsyncCompletionStream(stream, output_type, model)


def format_tool_calls(
    messages: List[ChatCompletionMessageParam],
) -> List[ChatCompletionMessageParam]:
    """Format message thread by replacing tool call blocks with readable assistant messages.

    This function processes a message thread and replaces sequences of:
    assistant(with tool_calls) + tool + tool + ... with a single clean assistant message
    that describes what tools were called and their results.

    Args:
        messages: List of messages in the conversation thread

    Returns:
        List[ChatCompletionMessageParam]: Cleaned message thread with tool calls formatted

    Example:
        ```python
        messages = [
            {"role": "user", "content": "What's the weather in NYC?"},
            {"role": "assistant", "tool_calls": [...]},
            {"role": "tool", "tool_call_id": "call_1", "content": "Sunny, 72°F"},
            {"role": "user", "content": "Thanks!"}
        ]

        formatted = format_tool_calls(messages)
        # Returns: [
        #     {"role": "user", "content": "What's the weather in NYC?"},
        #     {"role": "assistant", "content": "I called get_weather tool with parameters (city=NYC), and got result: Sunny, 72°F"},
        #     {"role": "user", "content": "Thanks!"}
        # ]
        ```
    """
    if not messages:
        return messages

    formatted_messages = []
    i = 0

    while i < len(messages):
        current_msg = messages[i]

        # Check if this is an assistant message with tool calls
        if current_msg.get("role") == "assistant" and current_msg.get("tool_calls"):
            # Collect all following tool messages
            tool_results = {}
            j = i + 1

            # Gather tool results that follow this assistant message
            while j < len(messages) and messages[j].get("role") == "tool":
                tool_msg = messages[j]
                tool_call_id = tool_msg.get("tool_call_id")
                if tool_call_id:
                    tool_results[tool_call_id] = tool_msg.get("content", "No result")
                j += 1

            # Format the tool calls with their results
            tool_calls = current_msg.get("tool_calls", [])
            formatted_calls = []

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                tool_id = tool_call.id

                # Parse arguments for cleaner display
                try:
                    args_dict = json.loads(tool_args) if tool_args else {}
                    args_str = ", ".join([f"{k}={v}" for k, v in args_dict.items()])
                except json.JSONDecodeError:
                    args_str = tool_args or "no parameters"

                # Get the result for this tool call
                result = tool_results.get(tool_id, "No result available")

                # Format the tool call description
                call_description = f"I called {tool_name} tool with parameters ({args_str}), and got result: {result}"
                formatted_calls.append(call_description)

            # Create the formatted assistant message
            if len(formatted_calls) == 1:
                content = formatted_calls[0]
            elif len(formatted_calls) > 1:
                content = "I made the following tool calls:\n" + "\n".join(
                    [f"- {call}" for call in formatted_calls]
                )
            else:
                content = "I made tool calls but no results were available."

            # Add the formatted message
            formatted_messages.append({"role": "assistant", "content": content})

            # Skip past all the tool messages we processed
            i = j
        else:
            # Regular message, add as-is
            formatted_messages.append(current_msg)
            i += 1

    return formatted_messages


def convert_response_to_completion(response: Any) -> Completion[str]:
    """Convert a LiteLLM ModelResponse to a Completion object.

    This function converts LiteLLM's ModelResponse (which is based on OpenAI's
    ChatCompletion format) into our unified Completion type for standard
    string completions.

    Args:
        response: The ModelResponse from LiteLLM

    Returns:
        Completion[str]: Unified completion object with string output

    Example:
        ```python
        # For LiteLLM completions
        response = await litellm.acompletion(model="gpt-4", messages=messages)
        completion = convert_response_to_completion(response)
        ```
    """
    # Handle empty or invalid response
    if not hasattr(response, "choices") or not response.choices:
        return Completion(
            output="",
            model=getattr(response, "model", "unknown"),
            content=None,
            completion=response,
        )

    choice = response.choices[0]

    # Extract message data
    if hasattr(choice, "message"):
        message = choice.message
        content = getattr(message, "content", None)
        tool_calls = getattr(message, "tool_calls", None)
        refusal = getattr(message, "refusal", None)
    else:
        # Fallback for different response structures
        content = None
        tool_calls = None
        refusal = None

    return Completion(
        output=content or "",
        model=getattr(response, "model", "unknown"),
        content=content,
        tool_calls=tool_calls,
        refusal=refusal,
        completion=response,
    )


class InstructorStreamWrapper:
    """Wrapper for instructor streaming that captures raw completion content using hooks."""

    def __init__(self, client, response_model, params, output_type, model):
        self.client = client
        self.response_model = response_model
        self.params = params
        self.output_type = output_type
        self.model = model
        self._raw_content_chunks = []
        self._raw_completion = None
        self._tool_calls = None

        # Set up hooks to capture raw content
        self.client.on("completion:response", self._capture_completion)

    def _capture_completion(self, completion):
        """Capture the raw completion response."""
        self._raw_completion = completion
        if hasattr(completion, "choices") and completion.choices:
            choice = completion.choices[0]
            # Capture content chunks
            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                content = choice.delta.content
                if content:
                    self._raw_content_chunks.append(content)
            # Capture tool calls from message (final chunk)
            if hasattr(choice, "message") and hasattr(choice.message, "tool_calls"):
                self._tool_calls = choice.message.tool_calls

    def __iter__(self):
        """Create the stream and yield wrapped chunks."""
        stream = self.client.chat.completions.create_partial(
            response_model=self.response_model, **self.params
        )

        for chunk in stream:
            yield chunk

        # Clean up hooks
        self.client.off("completion:response", self._capture_completion)

    def get_raw_content(self):
        """Get the accumulated raw content."""
        return "".join(self._raw_content_chunks)

    def get_raw_completion(self):
        """Get the raw completion object."""
        return self._raw_completion

    def get_tool_calls(self):
        """Get the tool calls from the completion."""
        return self._tool_calls

    def get_tool_calls(self):
        """Get the tool calls from the completion."""
        return self._tool_calls


class AsyncInstructorStreamWrapper:
    """Async wrapper for instructor streaming that captures raw completion content using hooks."""

    def __init__(self, client, response_model, params, output_type, model):
        self.client = client
        self.response_model = response_model
        self.params = params
        self.output_type = output_type
        self.model = model
        self._raw_content_chunks = []
        self._raw_completion = None
        self._tool_calls = None

        # Set up hooks to capture raw content
        self.client.on("completion:response", self._capture_completion)

    def _capture_completion(self, completion):
        """Capture the raw completion response."""
        self._raw_completion = completion
        if hasattr(completion, "choices") and completion.choices:
            choice = completion.choices[0]
            # Capture content chunks
            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                content = choice.delta.content
                if content:
                    self._raw_content_chunks.append(content)
            # Capture tool calls from message (final chunk)
            if hasattr(choice, "message") and hasattr(choice.message, "tool_calls"):
                self._tool_calls = choice.message.tool_calls

    async def __aiter__(self):
        """Create the stream and yield wrapped chunks."""
        stream = await self.client.chat.completions.create_partial(
            response_model=self.response_model, **self.params
        )

        async for chunk in stream:
            yield chunk

        # Clean up hooks
        self.client.off("completion:response", self._capture_completion)

    def get_raw_content(self):
        """Get the accumulated raw content."""
        return "".join(self._raw_content_chunks)

    def get_raw_completion(self):
        """Get the raw completion object."""
        return self._raw_completion
