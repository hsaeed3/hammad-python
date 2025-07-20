"""hammad.genai.types.history"""

from typing import List, Union, overload, TYPE_CHECKING, Any, Dict
from typing_extensions import Literal
import json

if TYPE_CHECKING:
    try:
        from openai.types.chat import ChatCompletionMessageParam
    except ImportError:
        ChatCompletionMessageParam = Any

from ..models.language.types import LanguageModelResponse, LanguageModelStream
from ..agents.types.agent_response import AgentResponse
from ..agents.types.agent_stream import AgentStream

__all__ = ["History"]


class History:
    """A conversation history manager that handles messages and responses.

    This class provides a clean interface for managing conversation history,
    including adding messages, responses, and rendering the complete history
    with optional tool call formatting.
    """

    def __init__(self):
        """Initialize an empty conversation history."""
        self.messages: List["ChatCompletionMessageParam"] = []

    @overload
    def add(
        self,
        content: str,
        *,
        role: Literal["user", "assistant", "system", "tool"] = "user",
    ) -> None:
        """Add a simple text message to the history.

        Args:
            content: The message content
            role: The role of the message sender
        """
        ...

    @overload
    def add(self, content: List["ChatCompletionMessageParam"]) -> None:
        """Add a list of messages to the history.

        Args:
            content: List of ChatCompletionMessageParam messages
        """
        ...

    def add(
        self,
        content: Union[str, List["ChatCompletionMessageParam"]],
        *,
        role: Literal["user", "assistant", "system", "tool"] = "user",
    ) -> None:
        """Add content to the conversation history.

        Args:
            content: Either a string message or a list of messages
            role: The role for string messages (ignored for message lists)
        """
        if isinstance(content, str):
            self.messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            self.messages.extend(content)
        else:
            raise TypeError(
                f"Expected str or List[ChatCompletionMessageParam], got {type(content)}"
            )

    def add_message(self, message: "ChatCompletionMessageParam") -> None:
        """Add a single message to the history.

        Args:
            message: A ChatCompletionMessageParam to add
        """
        self.messages.append(message)

    @overload
    def add_response(
        self, response: LanguageModelResponse, *, format_tool_calls: bool = False
    ) -> None:
        """Add a LanguageModelResponse to the history.

        Args:
            response: The language model response to add
            format_tool_calls: Whether to format tool calls in the message
        """
        ...

    @overload
    def add_response(
        self, response: LanguageModelStream, *, format_tool_calls: bool = False
    ) -> None:
        """Add a Stream response to the history after collecting it.

        Args:
            response: The stream to collect and add
            format_tool_calls: Whether to format tool calls in the message
        """
        ...

    @overload
    def add_response(
        self, response: AgentResponse, *, format_tool_calls: bool = False
    ) -> None:
        """Add an AgentResponse to the history.

        Args:
            response: The agent response to add
            format_tool_calls: Whether to format tool calls in the message
        """
        ...

    @overload
    def add_response(
        self, response: AgentStream, *, format_tool_calls: bool = False
    ) -> None:
        """Add an AgentStream to the history after collecting it.

        Args:
            response: The agent stream to collect and add
            format_tool_calls: Whether to format tool calls in the message
        """
        ...

    def add_response(
        self,
        response: Union[
            LanguageModelResponse, LanguageModelStream, AgentResponse, AgentStream
        ],
        *,
        format_tool_calls: bool = False,
    ) -> None:
        """Add a language model or agent response to the history.

        Args:
            response: The response or stream to add
            format_tool_calls: Whether to format tool calls in the message content
        """
        if isinstance(response, (LanguageModelResponse, AgentResponse)):
            # Direct response - convert to message
            message = response.to_message(format_tool_calls=format_tool_calls)
            self.messages.append(message)
        elif isinstance(response, (LanguageModelStream, AgentStream)):
            raise RuntimeError(
                "Cannot add uncollected streams to history. "
                "Please collect the stream first using stream.collect() or stream.to_response(), "
                "then add the resulting response to history."
            )
        else:
            raise TypeError(
                f"Expected LanguageModelResponse, AgentResponse, Stream, or AgentStream, got {type(response)}"
            )

    def _summarize_content(self, content: str, max_length: int = 100) -> str:
        """Summarize content by truncating with ellipsis if too long.

        Args:
            content: The content to summarize
            max_length: Maximum length before truncation

        Returns:
            Summarized content
        """
        if len(content) <= max_length:
            return content
        return content[: max_length - 3] + "..."

    def _format_and_merge_tool_calls(
        self,
        messages: List["ChatCompletionMessageParam"],
        summarize_tool_calls: bool = True,
    ) -> List["ChatCompletionMessageParam"]:
        """Format tool calls and merge tool responses into assistant messages.

        Args:
            messages: List of messages to process
            summarize_tool_calls: Whether to summarize tool call content

        Returns:
            Formatted messages with tool calls and responses merged
        """
        # Create a mapping of tool_call_id to tool response content
        tool_responses: Dict[str, str] = {}
        tool_message_indices: List[int] = []

        for i, message in enumerate(messages):
            if message.get("role") == "tool":
                tool_call_id = message.get("tool_call_id")
                if tool_call_id:
                    tool_responses[tool_call_id] = message.get("content", "")
                    tool_message_indices.append(i)

        # Process messages and format tool calls
        formatted_messages = []
        indices_to_skip = set(tool_message_indices)

        for i, message in enumerate(messages):
            if i in indices_to_skip:
                continue

            if message.get("role") == "assistant" and message.get("tool_calls"):
                # Create a copy of the message
                formatted_message = dict(message)

                # Format tool calls and merge responses
                content_parts = []
                if message.get("content"):
                    content_parts.append(message["content"])

                for tool_call in message["tool_calls"]:
                    tool_id = tool_call.get("id")
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]

                    # Format arguments nicely
                    try:
                        args_dict = (
                            json.loads(tool_args)
                            if isinstance(tool_args, str)
                            else tool_args
                        )
                        args_str = json.dumps(args_dict, indent=2)
                    except:
                        args_str = str(tool_args)

                    # Create the tool call section
                    tool_section = f"I called the function `{tool_name}` with arguments:\n{args_str}"

                    # Add tool response if available
                    if tool_id and tool_id in tool_responses:
                        response_content = tool_responses[tool_id]
                        if summarize_tool_calls and len(response_content) > 100:
                            response_content = self._summarize_content(response_content)
                        tool_section += f"\n\nResponse: {response_content}"

                    content_parts.append(tool_section)

                formatted_message["content"] = "\n\n".join(content_parts)
                # Remove tool_calls from the formatted message
                formatted_message.pop("tool_calls", None)

                formatted_messages.append(formatted_message)
            else:
                formatted_messages.append(message)

        return formatted_messages

    def render(
        self, *, format_tool_calls: bool = False, summarize_tool_calls: bool = True
    ) -> List["ChatCompletionMessageParam"]:
        """Render the conversation history as a list of messages.

        Args:
            format_tool_calls: Whether to format tool calls in assistant messages
                             for better readability and merge tool responses
            summarize_tool_calls: Whether to summarize tool call responses when
                                format_tool_calls is True (defaults to True)

        Returns:
            List of ChatCompletionMessageParam messages
        """
        if format_tool_calls:
            return self._format_and_merge_tool_calls(
                self.messages, summarize_tool_calls
            )
        return self.messages.copy()

    def clear(self) -> None:
        """Clear all messages from the history."""
        self.messages.clear()

    def __len__(self) -> int:
        """Return the number of messages in the history."""
        return len(self.messages)

    def __bool__(self) -> bool:
        """Return True if there are messages in the history."""
        return bool(self.messages)

    def __repr__(self) -> str:
        """Return a string representation of the history."""
        return f"History(messages={len(self.messages)})"
