"""hammad.ai.llms.utils._completions"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Generic, TypeVar

from .....cache import cached
from .....data.models import (
    convert_to_pydantic_model,
    is_pydantic_model_class,
)

try:
    from openai.types.chat import ChatCompletionMessageParam
except ImportError:
    ChatCompletionMessageParam = Any

from ..types.language_model_messages import LanguageModelMessages
from ..types.language_model_response import LanguageModelResponse
from ..types.language_model_request import LanguageModelRequest
from ..types.language_model_name import LanguageModelName
from ..types.language_model_instructor_mode import LanguageModelInstructorMode

__all__ = [
    "format_tool_calls",
    "consolidate_system_messages",
    "parse_messages_input",
    "handle_completion_request_params",
    "handle_completion_response",
    "LanguageModelRequestBuilder",
]


T = TypeVar("T")


@cached
def format_tool_calls(
    messages: List["ChatCompletionMessageParam"],
) -> List["ChatCompletionMessageParam"]:
    """Format tool calls in messages for better conversation context.

    Args:
        messages: List of chat completion messages

    Returns:
        Messages with formatted tool calls
    """
    formatted_messages = []

    for message in messages:
        if message.get("role") == "assistant" and message.get("tool_calls"):
            # Create a copy of the message
            formatted_message = dict(message)

            # Format tool calls into readable content
            content_parts = []
            if message.get("content"):
                content_parts.append(message["content"])

            for tool_call in message["tool_calls"]:
                formatted_call = (
                    f"I called the function `{tool_call['function']['name']}` "
                    f"with the following arguments:\n{tool_call['function']['arguments']}"
                )
                content_parts.append(formatted_call)

            formatted_message["content"] = "\n\n".join(content_parts)
            # Remove tool_calls from the formatted message
            formatted_message.pop("tool_calls", None)

            formatted_messages.append(formatted_message)
        else:
            formatted_messages.append(message)

    return formatted_messages


@cached
def consolidate_system_messages(
    messages: List["ChatCompletionMessageParam"],
) -> List["ChatCompletionMessageParam"]:
    """Consolidate multiple system messages into a single system message.

    Args:
        messages: List of chat completion messages

    Returns:
        Messages with consolidated system messages
    """
    system_parts = []
    other_messages = []

    for message in messages:
        if message.get("role") == "system":
            if message.get("content"):
                system_parts.append(message["content"])
        else:
            other_messages.append(message)

    # Create consolidated messages
    consolidated_messages = []

    if system_parts:
        consolidated_messages.append(
            {"role": "system", "content": "\n\n".join(system_parts)}
        )

    consolidated_messages.extend(other_messages)

    return consolidated_messages


@cached
def parse_messages_input(
    messages: LanguageModelMessages,
    instructions: Optional[str] = None,
) -> List["ChatCompletionMessageParam"]:
    """Parse various message input formats into standardized ChatCompletionMessageParam format.

    Args:
        messages: Input messages in various formats
        instructions: Optional system instructions to prepend

    Returns:
        List of ChatCompletionMessageParam objects
    """
    parsed_messages: List["ChatCompletionMessageParam"] = []

    # Add system instructions if provided
    if instructions:
        parsed_messages.append({"role": "system", "content": instructions})

    # Handle different input formats
    if isinstance(messages, str):
        # Simple string input
        parsed_messages.append({"role": "user", "content": messages})
    elif isinstance(messages, dict):
        # Single message dict
        parsed_messages.append(messages)
    elif isinstance(messages, list):
        # List of messages
        for msg in messages:
            if isinstance(msg, dict):
                parsed_messages.append(msg)
            elif isinstance(msg, str):
                parsed_messages.append({"role": "user", "content": msg})
    else:
        # Fallback - try to convert to string
        parsed_messages.append({"role": "user", "content": str(messages)})

    return parsed_messages


@cached
def handle_completion_request_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Filter and process parameters for standard completion requests.

    Args:
        params: Raw request parameters

    Returns:
        Filtered parameters suitable for LiteLLM completion
    """
    # Remove structured output specific parameters
    excluded_keys = {
        "type",
        "instructor_mode",
        "response_field_name",
        "response_field_instruction",
        "max_retries",
        "strict",
    }

    filtered_params = {
        key: value
        for key, value in params.items()
        if key not in excluded_keys and value is not None
    }

    return filtered_params


def handle_completion_response(response: Any, model: str) -> LanguageModelResponse[str]:
    """Convert a LiteLLM completion response to LanguageModelResponse.

    Args:
        response: LiteLLM ModelResponse object
        model: Model name used for the request

    Returns:
        LanguageModelResponse object with string output
    """
    # Extract content from the response
    content = None
    tool_calls = None
    refusal = None

    if hasattr(response, "choices") and response.choices:
        choice = response.choices[0]
        if hasattr(choice, "message"):
            message = choice.message
            content = getattr(message, "content", None)
            tool_calls = getattr(message, "tool_calls", None)
            refusal = getattr(message, "refusal", None)

    return LanguageModelResponse(
        type="language_model",
        model=model,
        output=content or "",
        completion=response,
        content=content,
        tool_calls=tool_calls,
        refusal=refusal,
    )


class LanguageModelRequestBuilder(Generic[T]):
    """A request to a language model with comprehensive parameter handling."""

    def __init__(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        model: LanguageModelName = "openai/gpt-4o-mini",
        **kwargs: Any,
    ):
        """Initialize a language model request.

        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            model: The model to use for the request
            **kwargs: Additional request settings
        """
        self.messages = messages
        self.instructions = instructions
        self.model = model
        self.settings = self._build_settings(**kwargs)

        # Validate settings
        self._validate_settings()

    def _build_settings(self, **kwargs: Any) -> LanguageModelRequest:
        """Build the complete settings dictionary from kwargs."""
        settings: LanguageModelRequest = {"model": self.model}

        # Add all provided kwargs to settings
        for key, value in kwargs.items():
            if value is not None:
                settings[key] = value

        return settings

    def _validate_settings(self) -> None:
        """Validate that the settings are compatible."""
        # Check if both tools and structured outputs are specified
        has_tools = any(
            key in self.settings
            for key in [
                "tools",
                "tool_choice",
                "parallel_tool_calls",
                "functions",
                "function_call",
            ]
        )

        has_structured_output = (
            "type" in self.settings and self.settings["type"] is not str
        )

        if has_tools and has_structured_output:
            raise ValueError(
                "Tools and structured outputs cannot be used together. "
                "Please specify either tools OR a structured output type, not both."
            )

    def is_structured_output(self) -> bool:
        """Check if this request is for structured output."""
        return "type" in self.settings and self.settings["type"] is not str

    def is_streaming(self) -> bool:
        """Check if this request is for streaming."""
        return self.settings.get("stream", False)

    def has_tools(self) -> bool:
        """Check if this request has tools."""
        return any(
            key in self.settings
            for key in [
                "tools",
                "tool_choice",
                "parallel_tool_calls",
                "functions",
                "function_call",
            ]
        )

    def get_completion_settings(self) -> Dict[str, Any]:
        """Get settings filtered for standard completion requests."""
        excluded_keys = {
            "type",
            "instructor_mode",
            "response_field_name",
            "response_field_instruction",
            "response_model_name",
            "max_retries",
            "strict",
            "validation_context",
            "context",
            "completion_kwargs_hooks",
            "completion_response_hooks",
            "completion_error_hooks",
            "completion_last_attempt_hooks",
            "parse_error_hooks",
        }

        return {
            key: value
            for key, value in self.settings.items()
            if key not in excluded_keys
        }

    def get_structured_output_settings(self) -> Dict[str, Any]:
        """Get settings filtered for structured output requests."""
        excluded_keys = {
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "functions",
            "function_call",
            "type",
            "instructor_mode",
            "response_field_name",
            "response_field_instruction",
            "response_model_name",
            "max_retries",
            "strict",
            "validation_context",
            "context",
            "completion_kwargs_hooks",
            "completion_response_hooks",
            "completion_error_hooks",
            "completion_last_attempt_hooks",
            "parse_error_hooks",
        }

        return {
            key: value
            for key, value in self.settings.items()
            if key not in excluded_keys
        }

    def get_output_type(self) -> Type[T]:
        """Get the requested output type."""
        return self.settings.get("type", str)

    def get_instructor_mode(self) -> LanguageModelInstructorMode:
        """Get the instructor mode for structured outputs."""
        return self.settings.get("instructor_mode", "tool_call")

    def get_response_field_name(self) -> str:
        """Get the response field name for structured outputs."""
        return self.settings.get("response_field_name", "content")

    def get_response_field_instruction(self) -> str:
        """Get the response field instruction for structured outputs."""
        return self.settings.get(
            "response_field_instruction",
            "A response in the correct type as requested by the user, or relevant content.",
        )

    def get_response_model_name(self) -> str:
        """Get the response model name for structured outputs."""
        return self.settings.get("response_model_name", "Response")

    def get_max_retries(self) -> int:
        """Get the maximum retries for structured outputs."""
        return self.settings.get("max_retries", 3)

    def get_strict_mode(self) -> bool:
        """Get the strict mode for structured outputs."""
        return self.settings.get("strict", True)

    def get_validation_context(self) -> Optional[Dict[str, Any]]:
        """Get the validation context for structured outputs."""
        return self.settings.get("validation_context")

    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get the context for structured outputs."""
        return self.settings.get("context")

    def prepare_pydantic_model(self) -> Optional[Type[Any]]:
        """Prepare a Pydantic model for structured outputs if needed."""
        if not self.is_structured_output():
            return None

        output_type = self.get_output_type()

        if is_pydantic_model_class(output_type):
            return output_type

        # Convert to Pydantic model
        return convert_to_pydantic_model(
            target=output_type,
            name="Response",
            field_name=self.get_response_field_name(),
            description=self.get_response_field_instruction(),
        )

    def __repr__(self) -> str:
        """String representation of the request."""
        return (
            f"LanguageModelRequest("
            f"model={self.model}, "
            f"structured_output={self.is_structured_output()}, "
            f"streaming={self.is_streaming()}, "
            f"has_tools={self.has_tools()}"
            f")"
        )
