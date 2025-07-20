"""hammad.genai.language_models._utils._structured_outputs"""

from typing import Any, Dict, Type, TypeVar

from .....cache import cached
from .....data.models import (
    convert_to_pydantic_model,
    is_pydantic_model_class,
)
from ..types.language_model_response import LanguageModelResponse

__all__ = [
    "handle_structured_output_request_params",
    "prepare_response_model",
    "handle_structured_output_response",
]

T = TypeVar("T")


@cached
def handle_structured_output_request_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Filter and process parameters for structured output requests.

    Args:
        params: Raw request parameters

    Returns:
        Filtered parameters suitable for Instructor
    """
    # Remove tool-related parameters (not supported with structured outputs)
    # and structured output specific parameters
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
    }

    filtered_params = {
        key: value
        for key, value in params.items()
        if key not in excluded_keys and value is not None
    }

    return filtered_params


@cached
def prepare_response_model(
    output_type: Type[T],
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    response_model_name: str = "Response",
) -> Type[Any]:
    """Prepare a Pydantic model for structured outputs.

    Args:
        output_type: The desired output type
        response_field_name: Name of the response field
        response_field_instruction: Description of the response field
        response_model_name: Name of the response model

    Returns:
        Pydantic model class suitable for Instructor
    """
    # Check if it's already a Pydantic model
    if is_pydantic_model_class(output_type):
        return output_type

    # Convert to Pydantic model
    return convert_to_pydantic_model(
        target=output_type,
        name=response_model_name,
        field_name=response_field_name,
        description=response_field_instruction,
    )


def handle_structured_output_response(
    response: Any,
    completion: Any,
    model: str,
    output_type: Type[T],
    response_field_name: str = "content",
) -> LanguageModelResponse[T]:
    """Convert an Instructor response to LanguageModelResponse.

    Args:
        response: The structured response from Instructor
        completion: The raw completion object
        model: Model name used for the request
        output_type: The expected output type
        response_field_name: Name of the response field

    Returns:
        LanguageModelResponse object with structured output
    """
    # Extract the actual value if using converted pydantic model
    if not is_pydantic_model_class(output_type) and hasattr(
        response, response_field_name
    ):
        actual_output = getattr(response, response_field_name)
    else:
        actual_output = response

    # Extract content and tool calls from the completion
    content = None
    tool_calls = None
    refusal = None

    if hasattr(completion, "choices") and completion.choices:
        choice = completion.choices[0]
        if hasattr(choice, "message"):
            message = choice.message
            content = getattr(message, "content", None)
            tool_calls = getattr(message, "tool_calls", None)
            refusal = getattr(message, "refusal", None)

    return LanguageModelResponse(
        model=model,
        output=actual_output,
        completion=completion,
        content=content,
        tool_calls=tool_calls,
        refusal=refusal,
    )
