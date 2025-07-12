"""hammad.genai.language_models.run

Standalone functions for running language models with full parameter typing.
"""

from typing import (
    Any,
    List,
    TypeVar,
    Union,
    Optional,
    Type,
    overload,
    Dict,
    TYPE_CHECKING,
    Callable,
)
from typing_extensions import Literal

if TYPE_CHECKING:
    from httpx import Timeout

    from openai.types.chat import (
        ChatCompletionModality,
        ChatCompletionPredictionContentParam,
        ChatCompletionAudioParam,
    )

from .types import (
    LanguageModelMessages,
    LanguageModelInstructorMode,
    LanguageModelName,
    LanguageModelResponse,
    LanguageModelStream,
)
from .model import LanguageModel


__all__ = [
    "run_language_model",
    "async_run_language_model",
]


T = TypeVar("T")


# Overloads for run_language_model - String output, non-streaming
@overload
def run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Streaming settings
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelResponse[str]": ...


# Overloads for run_language_model - String output, streaming
@overload
def run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Streaming settings
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelStream[str]": ...


# Overloads for run_language_model - Structured output, non-streaming
@overload
def run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Structured output settings
    type: Type[T],
    instructor_mode: Optional[LanguageModelInstructorMode] = "tool_call",
    response_field_name: Optional[str] = None,
    response_field_instruction: Optional[str] = None,
    response_model_name: Optional[str] = None,
    max_retries: Optional[int] = None,
    strict: Optional[bool] = None,
    validation_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
    completion_response_hooks: Optional[List[Callable[..., None]]] = None,
    completion_error_hooks: Optional[List[Callable[..., None]]] = None,
    completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
    parse_error_hooks: Optional[List[Callable[..., None]]] = None,
    # Streaming settings
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelResponse[T]": ...


# Overloads for run_language_model - Structured output, streaming
@overload
def run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Structured output settings
    type: Type[T],
    instructor_mode: Optional[LanguageModelInstructorMode] = "tool_call",
    response_field_name: Optional[str] = None,
    response_field_instruction: Optional[str] = None,
    response_model_name: Optional[str] = None,
    max_retries: Optional[int] = None,
    strict: Optional[bool] = None,
    validation_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
    completion_response_hooks: Optional[List[Callable[..., None]]] = None,
    completion_error_hooks: Optional[List[Callable[..., None]]] = None,
    completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
    parse_error_hooks: Optional[List[Callable[..., None]]] = None,
    # Streaming settings
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelStream[T]": ...


def run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    mock_response: Optional[bool] = None,
    verbose: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> Union["LanguageModelResponse[Any]", "LanguageModelStream[Any]"]:
    """Run a language model request with full parameter support.

    Args:
        messages: The input messages/content for the request
        instructions: Optional system instructions to prepend
        verbose: If True, set logger to INFO level for detailed output
        debug: If True, set logger to DEBUG level for maximum verbosity
        **kwargs: All request parameters from LanguageModelRequest

    Returns:
        LanguageModelResponse or Stream depending on parameters
    """
    # Extract model parameter or use default
    model = kwargs.pop("model", "openai/gpt-4o-mini")

    # Create language model instance
    language_model = LanguageModel(model=model, verbose=verbose, debug=debug)

    # Forward to the instance method
    return language_model.run(
        messages,
        instructions,
        mock_response=mock_response,
        verbose=verbose,
        debug=debug,
        **kwargs,
    )


# Async overloads for async_run_language_model - String output, non-streaming
@overload
async def async_run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    # Streaming settings
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelResponse[str]": ...


# Async overloads for async_run_language_model - String output, streaming
@overload
async def async_run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Streaming settings
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelStream[str]": ...


# Async overloads for async_run_language_model - Structured output, non-streaming
@overload
async def async_run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Structured output settings
    type: Type[T],
    instructor_mode: Optional[LanguageModelInstructorMode] = "tool_call",
    response_field_name: Optional[str] = None,
    response_field_instruction: Optional[str] = None,
    response_model_name: Optional[str] = None,
    max_retries: Optional[int] = None,
    strict: Optional[bool] = None,
    validation_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
    completion_response_hooks: Optional[List[Callable[..., None]]] = None,
    completion_error_hooks: Optional[List[Callable[..., None]]] = None,
    completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
    parse_error_hooks: Optional[List[Callable[..., None]]] = None,
    # Streaming settings
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelResponse[T]": ...


# Async overloads for async_run_language_model - Structured output, streaming
@overload
async def async_run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    *,
    # Provider settings
    model: "LanguageModelName" = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    mock_response: Optional[bool] = None,
    # Structured output settings
    type: Type[T],
    instructor_mode: Optional[LanguageModelInstructorMode] = "tool_call",
    response_field_name: Optional[str] = None,
    response_field_instruction: Optional[str] = None,
    response_model_name: Optional[str] = None,
    max_retries: Optional[int] = None,
    strict: Optional[bool] = None,
    validation_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
    completion_response_hooks: Optional[List[Callable[..., None]]] = None,
    completion_error_hooks: Optional[List[Callable[..., None]]] = None,
    completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
    parse_error_hooks: Optional[List[Callable[..., None]]] = None,
    # Streaming settings
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    # Extended settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List["ChatCompletionModality"]] = None,
    prediction: Optional["ChatCompletionPredictionContentParam"] = None,
    audio: Optional["ChatCompletionAudioParam"] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    seed: Optional[int] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    web_search_options: Optional[Dict[str, Any]] = None,
    # Tools settings
    tools: Optional[List[Any]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
    functions: Optional[List[Any]] = None,
    function_call: Optional[str] = None,
) -> "LanguageModelStream[T]": ...


async def async_run_language_model(
    messages: "LanguageModelMessages",
    instructions: Optional[str] = None,
    mock_response: Optional[bool] = None,
    verbose: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> Union["LanguageModelResponse[Any]", "LanguageModelStream[Any]"]:
    """Run an async language model request with full parameter support.

    Args:
        messages: The input messages/content for the request
        instructions: Optional system instructions to prepend
        verbose: If True, set logger to INFO level for detailed output
        debug: If True, set logger to DEBUG level for maximum verbosity
        **kwargs: All request parameters from LanguageModelRequest

    Returns:
        LanguageModelResponse or AsyncStream depending on parameters
    """
    # Extract model parameter or use default
    model = kwargs.pop("model", "openai/gpt-4o-mini")

    # Create language model instance
    language_model = LanguageModel(model=model, verbose=verbose, debug=debug)

    # Forward to the instance method
    return await language_model.async_run(
        messages,
        instructions,
        mock_response=mock_response,
        verbose=verbose,
        debug=debug,
        **kwargs,
    )
