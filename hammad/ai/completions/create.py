"""hammad.ai.completions.create"""

from httpx import Timeout
from typing import Any, Dict, List, Literal, Optional, Union, overload

try:
    from openai.types.chat import (
        ChatCompletionModality,
        ChatCompletionPredictionContentParam,
        ChatCompletionAudioParam,
    )
except ImportError:
    raise ImportError(
        "Using the `hammad.ai.completions` extension requires the `openai` package to be installed.\n"
        "Please either install the `openai` package, or install the `hammad.ai` extension with:\n"
        "`pip install 'hammad-python[ai]'"
    )

from .types import (
    CompletionsModelName,
    CompletionsInputParam,
    CompletionsOutputType,
    Completion,
    CompletionStream,
)
from .client import (
    CompletionsInstructorModeParam,
    AnthropicThinkingParam,
    OpenAIWebSearchOptions,
    CompletionsClient,
)


__all__ = ("create_completion", "async_create_completion")


# Async overloads
@overload
async def async_create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> CompletionStream[CompletionsOutputType]: ...


@overload
async def async_create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> Completion[CompletionsOutputType]: ...


async def async_create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Optional[bool] = None,
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> Completion[CompletionsOutputType] | CompletionStream[CompletionsOutputType]:
    """Asynchronously generate a chat completion or structured output from a valid `litellm`
    compatible language model.

    This function provides a unified interface for creating completions with support
    for both text generation and structured outputs using Pydantic models or basic
    Python types. It leverages the instructor library for structured outputs and
    litellm for model compatibility across different providers.

    Args:
        messages (CompletionsInputParam): The input messages, which can be:
            - A string for simple prompts
            - A formatted string with role markers (e.g., "[system]...[user]...")
            - A single ChatCompletionMessageParam object
            - A list of ChatCompletionMessageParam objects
        instructions (Optional[str], optional): Additional system instructions to
            prepend to the conversation. Defaults to None.
        model (str, optional): The model identifier in litellm format (e.g.,
            "openai/gpt-4o-mini", "anthropic/claude-3-sonnet").
            Defaults to "openai/gpt-4o-mini".
        type (CompletionsOutputType, optional): The desired output type. Can be:
            - str for text completion (default)
            - A Pydantic BaseModel class for structured output
            - Basic Python types (int, float, bool, list, dict)
            Defaults to str.
        response_field_name (str, optional): The name of the field in the response to return.
            Defaults to "content".
        response_field_instruction (str, optional): The instruction for the response field.
            Defaults to "A response in the correct type as requested by the user, or relevant content."
        instructor_mode (CompletionsInstructorModeParam, optional): The instructor mode for
            structured outputs ("tool_call", "json", "json_schema", "markdown_json_schema",
            "function_call"). Defaults to "tool_call".
        max_retries (int, optional): Maximum number of retries for structured output
            validation. Defaults to 3.
        strict (bool, optional): Whether to use strict mode for structured outputs.
            Defaults to True.
        timeout (Optional[Union[float, str, Timeout]], optional): Request timeout.
        temperature (Optional[float], optional): Sampling temperature (0.0 to 2.0).
        top_p (Optional[float], optional): Nucleus sampling parameter.
        n (Optional[int], optional): Number of completions to generate.
        stream (Optional[bool], optional): Whether to stream the response.
        stream_options (Optional[Dict[str, Any]], optional): Additional streaming options.
        stop (Optional[str], optional): Stop sequences for completion.
        max_completion_tokens (Optional[int], optional): Maximum tokens in completion.
        max_tokens (Optional[int], optional): Legacy parameter for max_completion_tokens.
        modalities (Optional[List[ChatCompletionModality]], optional): Response modalities.
        prediction (Optional[ChatCompletionPredictionContentParam], optional): Prediction content.
        audio (Optional[ChatCompletionAudioParam], optional): Audio parameters.
        presence_penalty (Optional[float], optional): Presence penalty (-2.0 to 2.0).
        frequency_penalty (Optional[float], optional): Frequency penalty (-2.0 to 2.0).
        logit_bias (Optional[Dict[str, float]], optional): Token logit biases.
        user (Optional[str], optional): User identifier for tracking.
        reasoning_effort (Optional[Literal["low", "medium", "high"]], optional):
            Reasoning effort level for supported models.
        seed (Optional[int], optional): Random seed for deterministic outputs.
        tools (Optional[List], optional): Available tools for function calling.
        tool_choice (Optional[Union[str, Dict[str, Any]]], optional): Tool selection strategy.
        logprobs (Optional[bool], optional): Whether to return log probabilities.
        top_logprobs (Optional[int], optional): Number of top log probabilities to return.
        parallel_tool_calls (Optional[bool], optional): Whether to allow parallel tool calls.
        web_search_options (Optional[OpenAIWebSearchOptions], optional): Web search configuration.
        deployment_id (Optional[str], optional): Azure OpenAI deployment ID.
        extra_headers (Optional[Dict[str, str]], optional): Additional HTTP headers.
        base_url (Optional[str], optional): Custom API base URL.
        functions (Optional[List], optional): Legacy functions parameter.
        function_call (Optional[str], optional): Legacy function call parameter.
        api_version (Optional[str], optional): API version for Azure OpenAI.
        api_key (Optional[str], optional): API key override.
        model_list (Optional[list], optional): List of model configurations.
        thinking (Optional[AnthropicThinkingParam], optional): Anthropic thinking parameters.

    Returns:
        Union[Completion[CompletionsOutputType], CompletionStream[CompletionsOutputType]]:
            - Completion object containing the generated output if stream=False
            - CompletionStream object for iterating over chunks if stream=True

    Examples:
        Basic text completion:

        >>> completion = create_completion(
        ...     messages="What is the capital of France?",
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.content)
        "The capital of France is Paris."

        Structured output with Pydantic model:

        >>> from pydantic import BaseModel
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> completion = create_completion(
        ...     messages="Extract: John is 25 years old",
        ...     type=Person,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.output.name)  # "John"
        >>> print(completion.output.age)   # 25

        Streaming completion:

        >>> stream = create_completion(
        ...     messages="Tell me a story",
        ...     stream=True,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> for chunk in stream:
        ...     print(chunk.content, end="")

        Simple type extraction:

        >>> completion = create_completion(
        ...     messages="How many days are in a week?",
        ...     type=int,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.output)  # 7

        Conversation with multiple messages:

        >>> completion = create_completion(
        ...     messages=[
        ...         {"role": "system", "content": "You are a helpful assistant."},
        ...         {"role": "user", "content": "What's 2+2?"},
        ...         {"role": "assistant", "content": "2+2 equals 4."},
        ...         {"role": "user", "content": "What about 3+3?"}
        ...     ],
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.content)
        "3+3 equals 6."

    Raises:
        CompletionsError: If there's an error during completion generation or
            input parsing.
        ValidationError: If structured output validation fails after max_retries.
    """
    return await CompletionsClient.async_structured_output(
        messages=messages,
        instructions=instructions,
        model=model,
        type=type,
        response_field_name=response_field_name,
        response_field_instruction=response_field_instruction,
        instructor_mode=instructor_mode,
        max_retries=max_retries,
        strict=strict,
        timeout=timeout,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
        stream_options=stream_options,
        stop=stop,
        max_completion_tokens=max_completion_tokens,
        max_tokens=max_tokens,
        modalities=modalities,
        prediction=prediction,
        audio=audio,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        reasoning_effort=reasoning_effort,
        seed=seed,
        tools=tools,
        tool_choice=tool_choice,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        parallel_tool_calls=parallel_tool_calls,
        web_search_options=web_search_options,
        deployment_id=deployment_id,
        extra_headers=extra_headers,
        base_url=base_url,
        functions=functions,
        function_call=function_call,
        api_version=api_version,
        api_key=api_key,
        model_list=model_list,
        thinking=thinking,
    )


# Sync overloads
@overload
def create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Literal[True],
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> CompletionStream[CompletionsOutputType]: ...


@overload
def create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Literal[False] = False,
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> Completion[CompletionsOutputType]: ...


def create_completion(
    messages: CompletionsInputParam,
    instructions: Optional[str] = None,
    model: str | CompletionsModelName = "openai/gpt-4o-mini",
    type: CompletionsOutputType = str,
    response_field_name: str = "content",
    response_field_instruction: str = "A response in the correct type as requested by the user, or relevant content.",
    instructor_mode: CompletionsInstructorModeParam = "tool_call",
    max_retries: int = 3,
    strict: bool = True,
    *,
    timeout: Optional[Union[float, str, Timeout]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: Optional[bool] = None,
    stream_options: Optional[Dict[str, Any]] = None,
    stop: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    modalities: Optional[List[ChatCompletionModality]] = None,
    prediction: Optional[ChatCompletionPredictionContentParam] = None,
    audio: Optional[ChatCompletionAudioParam] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int] = None,
    tools: Optional[List] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    parallel_tool_calls: Optional[bool] = None,
    web_search_options: Optional[OpenAIWebSearchOptions] = None,
    deployment_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    functions: Optional[List] = None,
    function_call: Optional[str] = None,
    # set api_base, api_version, api_key
    api_version: Optional[str] = None,
    api_key: Optional[str] = None,
    model_list: Optional[list] = None,
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam] = None,
) -> Completion[CompletionsOutputType] | CompletionStream[CompletionsOutputType]:
    """Generate a chat completion or structured output from a valid `litellm`
    compatible language model.

    This function provides a unified interface for creating completions with support
    for both text generation and structured outputs using Pydantic models or basic
    Python types. It leverages the instructor library for structured outputs and
    litellm for model compatibility across different providers.

    Args:
        messages (CompletionsInputParam): The input messages, which can be:
            - A string for simple prompts
            - A formatted string with role markers (e.g., "[system]...[user]...")
            - A single ChatCompletionMessageParam object
            - A list of ChatCompletionMessageParam objects
        instructions (Optional[str], optional): Additional system instructions to
            prepend to the conversation. Defaults to None.
        model (str, optional): The model identifier in litellm format (e.g.,
            "openai/gpt-4o-mini", "anthropic/claude-3-sonnet").
            Defaults to "openai/gpt-4o-mini".
        type (CompletionsOutputType, optional): The desired output type. Can be:
            - str for text completion (default)
            - A Pydantic BaseModel class for structured output
            - Basic Python types (int, float, bool, list, dict)
            Defaults to str.
        response_field_name (str, optional): The name of the field in the response to return.
            Defaults to "content".
        response_field_instruction (str, optional): The instruction for the response field.
            Defaults to "A response in the correct type as requested by the user, or relevant content."
        instructor_mode (CompletionsInstructorModeParam, optional): The instructor mode for
            structured outputs ("tool_call", "json", "json_schema", "markdown_json_schema",
            "function_call"). Defaults to "tool_call".
        max_retries (int, optional): Maximum number of retries for structured output
            validation. Defaults to 3.
        strict (bool, optional): Whether to use strict mode for structured outputs.
            Defaults to True.
        timeout (Optional[Union[float, str, Timeout]], optional): Request timeout.
        temperature (Optional[float], optional): Sampling temperature (0.0 to 2.0).
        top_p (Optional[float], optional): Nucleus sampling parameter.
        n (Optional[int], optional): Number of completions to generate.
        stream (Optional[bool], optional): Whether to stream the response.
        stream_options (Optional[Dict[str, Any]], optional): Additional streaming options.
        stop (Optional[str], optional): Stop sequences for completion.
        max_completion_tokens (Optional[int], optional): Maximum tokens in completion.
        max_tokens (Optional[int], optional): Legacy parameter for max_completion_tokens.
        modalities (Optional[List[ChatCompletionModality]], optional): Response modalities.
        prediction (Optional[ChatCompletionPredictionContentParam], optional): Prediction content.
        audio (Optional[ChatCompletionAudioParam], optional): Audio parameters.
        presence_penalty (Optional[float], optional): Presence penalty (-2.0 to 2.0).
        frequency_penalty (Optional[float], optional): Frequency penalty (-2.0 to 2.0).
        logit_bias (Optional[Dict[str, float]], optional): Token logit biases.
        user (Optional[str], optional): User identifier for tracking.
        reasoning_effort (Optional[Literal["low", "medium", "high"]], optional):
            Reasoning effort level for supported models.
        seed (Optional[int], optional): Random seed for deterministic outputs.
        tools (Optional[List], optional): Available tools for function calling.
        tool_choice (Optional[Union[str, Dict[str, Any]]], optional): Tool selection strategy.
        logprobs (Optional[bool], optional): Whether to return log probabilities.
        top_logprobs (Optional[int], optional): Number of top log probabilities to return.
        parallel_tool_calls (Optional[bool], optional): Whether to allow parallel tool calls.
        web_search_options (Optional[OpenAIWebSearchOptions], optional): Web search configuration.
        deployment_id (Optional[str], optional): Azure OpenAI deployment ID.
        extra_headers (Optional[Dict[str, str]], optional): Additional HTTP headers.
        base_url (Optional[str], optional): Custom API base URL.
        functions (Optional[List], optional): Legacy functions parameter.
        function_call (Optional[str], optional): Legacy function call parameter.
        api_version (Optional[str], optional): API version for Azure OpenAI.
        api_key (Optional[str], optional): API key override.
        model_list (Optional[list], optional): List of model configurations.
        thinking (Optional[AnthropicThinkingParam], optional): Anthropic thinking parameters.

    Returns:
        Union[Completion[CompletionsOutputType], CompletionStream[CompletionsOutputType]]:
            - Completion object containing the generated output if stream=False
            - CompletionStream object for iterating over chunks if stream=True

    Examples:
        Basic text completion:

        >>> completion = create_completion(
        ...     messages="What is the capital of France?",
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.content)
        "The capital of France is Paris."

        Structured output with Pydantic model:

        >>> from pydantic import BaseModel
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> completion = create_completion(
        ...     messages="Extract: John is 25 years old",
        ...     type=Person,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.output.name)  # "John"
        >>> print(completion.output.age)   # 25

        Streaming completion:

        >>> stream = create_completion(
        ...     messages="Tell me a story",
        ...     stream=True,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> for chunk in stream:
        ...     print(chunk.content, end="")

        Simple type extraction:

        >>> completion = create_completion(
        ...     messages="How many days are in a week?",
        ...     type=int,
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.output)  # 7

        Conversation with multiple messages:

        >>> completion = create_completion(
        ...     messages=[
        ...         {"role": "system", "content": "You are a helpful assistant."},
        ...         {"role": "user", "content": "What's 2+2?"},
        ...         {"role": "assistant", "content": "2+2 equals 4."},
        ...         {"role": "user", "content": "What about 3+3?"}
        ...     ],
        ...     model="openai/gpt-4o-mini"
        ... )
        >>> print(completion.content)
        "3+3 equals 6."

    Raises:
        CompletionsError: If there's an error during completion generation or
            input parsing.
        ValidationError: If structured output validation fails after max_retries.
    """
    return CompletionsClient.structured_output(
        messages=messages,
        instructions=instructions,
        model=model,
        type=type,
        response_field_name=response_field_name,
        response_field_instruction=response_field_instruction,
        instructor_mode=instructor_mode,
        max_retries=max_retries,
        strict=strict,
        timeout=timeout,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
        stream_options=stream_options,
        stop=stop,
        max_completion_tokens=max_completion_tokens,
        max_tokens=max_tokens,
        modalities=modalities,
        prediction=prediction,
        audio=audio,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        reasoning_effort=reasoning_effort,
        seed=seed,
        tools=tools,
        tool_choice=tool_choice,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        parallel_tool_calls=parallel_tool_calls,
        web_search_options=web_search_options,
        deployment_id=deployment_id,
        extra_headers=extra_headers,
        base_url=base_url,
        functions=functions,
        function_call=function_call,
        api_version=api_version,
        api_key=api_key,
        model_list=model_list,
        thinking=thinking,
    )
