"""hammad.genai.models.language.utils"""

from .requests import (
    format_tool_calls,
    consolidate_system_messages,
    parse_messages_input,
    handle_completion_request_params,
    handle_completion_response,
    LanguageModelRequestBuilder,
)
from .structured_outputs import (
    handle_structured_output_request_params,
    prepare_response_model,
    handle_structured_output_response,
)


__all__ = [
    "parse_messages_input",
    "handle_completion_request_params",
    "handle_completion_response",
    "handle_structured_output_request_params",
    "prepare_response_model",
    "handle_structured_output_response",
    "format_tool_calls",
    "consolidate_system_messages",
    "LanguageModelRequestBuilder",
]
