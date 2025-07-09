"""hammad.ai.llms.utils._completions"""

from typing import Any, Dict, List, Optional

from ....cache import cached

try:
    from openai.types.chat import ChatCompletionMessageParam
except ImportError:
    raise ImportError(
        "Using the `hammad.ai.llms` extension requires the `openai` package to be installed.\n"
        "Please either install the `openai` package, or install the `hammad.ai` extension with:\n"
        "`pip install 'hammad-python[ai]'`"
    )

from ..language_model_request import LanguageModelMessagesParam
from ..language_model_response import LanguageModelResponse

__all__ = [
    "parse_messages_input",
    "handle_completion_request_params",
    "handle_completion_response",
]


@cached
def parse_messages_input(
    messages: LanguageModelMessagesParam,
    instructions: Optional[str] = None,
) -> List[ChatCompletionMessageParam]:
    """Parse various message input formats into standardized ChatCompletionMessageParam format.
    
    Args:
        messages: Input messages in various formats
        instructions: Optional system instructions to prepend
        
    Returns:
        List of ChatCompletionMessageParam objects
    """
    parsed_messages: List[ChatCompletionMessageParam] = []
    
    # Add system instructions if provided
    if instructions:
        parsed_messages.append({
            "role": "system",
            "content": instructions
        })
    
    # Handle different input formats
    if isinstance(messages, str):
        # Simple string input
        parsed_messages.append({
            "role": "user", 
            "content": messages
        })
    elif isinstance(messages, dict):
        # Single message dict
        parsed_messages.append(messages)
    elif isinstance(messages, list):
        # List of messages
        for msg in messages:
            if isinstance(msg, dict):
                parsed_messages.append(msg)
            elif isinstance(msg, str):
                parsed_messages.append({
                    "role": "user",
                    "content": msg
                })
    else:
        # Fallback - try to convert to string
        parsed_messages.append({
            "role": "user",
            "content": str(messages)
        })
    
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
        "type", "instructor_mode", "response_field_name", 
        "response_field_instruction", "max_retries", "strict"
    }
    
    filtered_params = {
        key: value for key, value in params.items()
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
        model=model,
        output=content or "",
        completion=response,
        content=content,
        tool_calls=tool_calls,
        refusal=refusal,
    )