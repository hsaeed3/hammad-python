"""hammad.genai.language_models.run

Standalone functions for running language models with full parameter typing.
"""

import inspect
import functools
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
    "language_model_decorator",
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


def language_model_decorator(
    fn: Union[str, Callable, None] = None,
    *,
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    instructions: Optional[str] = None,
    mock_response: Optional[bool] = None,
    # Request settings
    output_type: Optional[Type] = None,
    stream: Optional[bool] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    return_output: bool = True,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
    # Advanced settings
    response_format: Optional[Dict[str, Any]] = None,
    stop: Optional[Union[str, List[str]]] = None,
    logit_bias: Optional[Dict[int, float]] = None,
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
    verbose: bool = False,
    debug: bool = False,
):
    """Decorator that converts a function into a language model call.

    The function's parameters become the input to the LLM (converted to a string),
    the function's return type annotation becomes the language model's output type,
    and the function's docstring becomes the language model's instructions.

    Works with both sync and async functions.

    Can be used in multiple ways:

    1. As a decorator with parameters:
       @language_model_decorator(model="gpt-4", temperature=0.7)
       def my_lm():
           pass

    2. As a decorator without parameters:
       @language_model_decorator
       def my_lm():
           pass

    3. As an inline function with model as first argument:
       lm = language_model_decorator("gpt-4")
       # Then use: decorated_func = lm(my_function)

    4. As an inline function with all parameters:
       lm = language_model_decorator(model="gpt-4", temperature=0.7)
       # Then use: decorated_func = lm(my_function)
    """
    # Handle different calling patterns
    if callable(fn):
        # Case: @language_model_decorator (no parentheses)
        func = fn
        actual_model = model or "openai/gpt-4o-mini"
        return _create_language_model_wrapper(
            func,
            actual_model,
            instructions,
            mock_response,
            output_type,
            stream,
            instructor_mode,
            return_output,
            timeout,
            temperature,
            top_p,
            max_tokens,
            presence_penalty,
            frequency_penalty,
            seed,
            user,
            response_format,
            stop,
            logit_bias,
            logprobs,
            top_logprobs,
            thinking,
            web_search_options,
            tools,
            tool_choice,
            parallel_tool_calls,
            functions,
            function_call,
            verbose,
            debug,
        )
    elif isinstance(fn, str):
        # Case: language_model_decorator("gpt-4") - first arg is model
        actual_model = fn
    else:
        # Case: language_model_decorator() or language_model_decorator(model="gpt-4")
        actual_model = model or "openai/gpt-4o-mini"

    def decorator(func: Callable) -> Callable:
        return _create_language_model_wrapper(
            func,
            actual_model,
            instructions,
            mock_response,
            output_type,
            stream,
            instructor_mode,
            return_output,
            timeout,
            temperature,
            top_p,
            max_tokens,
            presence_penalty,
            frequency_penalty,
            seed,
            user,
            response_format,
            stop,
            logit_bias,
            logprobs,
            top_logprobs,
            thinking,
            web_search_options,
            tools,
            tool_choice,
            parallel_tool_calls,
            functions,
            function_call,
            verbose,
            debug,
        )

    return decorator


def _create_language_model_wrapper(
    func: Callable,
    model: Union["LanguageModel", "LanguageModelName"],
    instructions: Optional[str],
    mock_response: Optional[bool],
    output_type: Optional[Type],
    stream: Optional[bool],
    instructor_mode: Optional["LanguageModelInstructorMode"],
    return_output: bool,
    timeout: Optional[Union[float, str, "Timeout"]],
    temperature: Optional[float],
    top_p: Optional[float],
    max_tokens: Optional[int],
    presence_penalty: Optional[float],
    frequency_penalty: Optional[float],
    seed: Optional[int],
    user: Optional[str],
    response_format: Optional[Dict[str, Any]],
    stop: Optional[Union[str, List[str]]],
    logit_bias: Optional[Dict[int, float]],
    logprobs: Optional[bool],
    top_logprobs: Optional[int],
    thinking: Optional[Dict[str, Any]],
    web_search_options: Optional[Dict[str, Any]],
    tools: Optional[List[Any]],
    tool_choice: Optional[Union[str, Dict[str, Any]]],
    parallel_tool_calls: Optional[bool],
    functions: Optional[List[Any]],
    function_call: Optional[str],
    verbose: bool,
    debug: bool,
) -> Callable:
    """Helper function to create the actual language model wrapper."""
    import inspect
    import asyncio
    from typing import get_type_hints

    # Get function metadata
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    return_type = output_type or type_hints.get("return", str)
    func_instructions = instructions or func.__doc__ or ""

    # Check if function is async
    is_async = asyncio.iscoroutinefunction(func)

    if is_async:

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Convert function parameters to message string
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Create message from parameters
            param_parts = []
            for param_name, param_value in bound_args.arguments.items():
                param_parts.append(f"{param_name}: {param_value}")
            message = "\n".join(param_parts)

            # Prepare parameters for language model call
            lm_kwargs = {
                "messages": message,
                "instructions": func_instructions,
                "model": model,
                "mock_response": mock_response,
                "stream": stream,
                "instructor_mode": instructor_mode,
                "timeout": timeout,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "seed": seed,
                "user": user,
                "response_format": response_format,
                "stop": stop,
                "logit_bias": logit_bias,
                "logprobs": logprobs,
                "top_logprobs": top_logprobs,
                "thinking": thinking,
                "web_search_options": web_search_options,
                "tools": tools,
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls,
                "functions": functions,
                "function_call": function_call,
            }

            # Only add type parameter if it's not str (for structured output)
            if return_type is not str:
                lm_kwargs["type"] = return_type

            # Run language model with extracted parameters
            return await async_run_language_model(**lm_kwargs)

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert function parameters to message string
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Create message from parameters
            param_parts = []
            for param_name, param_value in bound_args.arguments.items():
                param_parts.append(f"{param_name}: {param_value}")
            message = "\n".join(param_parts)

            # Prepare parameters for language model call
            lm_kwargs = {
                "messages": message,
                "instructions": func_instructions,
                "model": model,
                "mock_response": mock_response,
                "stream": stream,
                "instructor_mode": instructor_mode,
                "timeout": timeout,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "seed": seed,
                "user": user,
                "response_format": response_format,
                "stop": stop,
                "logit_bias": logit_bias,
                "logprobs": logprobs,
                "top_logprobs": top_logprobs,
                "thinking": thinking,
                "web_search_options": web_search_options,
                "tools": tools,
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls,
                "functions": functions,
                "function_call": function_call,
            }

            # Only add type parameter if it's not str (for structured output)
            if return_type is not str:
                lm_kwargs["type"] = return_type

            # Run language model with extracted parameters
            response = run_language_model(**lm_kwargs)

            # Return just the output if return_output is True (default behavior)
            if return_output:
                return response.output
            else:
                return response

        return sync_wrapper
