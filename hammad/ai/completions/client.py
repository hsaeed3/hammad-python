"""hammad.ai.completions.client"""

from httpx import Timeout
from typing import Any, Dict, List, Generic, Literal, TypeVar, Optional, Union, Type
import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict, Required, NotRequired
else:
    from typing_extensions import TypedDict, Required, NotRequired

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

from ...pydantic.converters import convert_to_pydantic_model
from .._utils import get_litellm, get_instructor
from ...base.model import Model
from ...typing import is_pydantic_basemodel
from .utils import (
    format_tool_calls,
    parse_completions_input,
    convert_response_to_completion,
    create_async_completion_stream,
    create_completion_stream,
)
from .types import (
    CompletionsInputParam,
    CompletionsOutputType,
    Completion,
    CompletionChunk,
    CompletionStream,
    AsyncCompletionStream,
)


class OpenAIWebSearchUserLocationApproximate(TypedDict):
    city: str
    country: str
    region: str
    timezone: str


class OpenAIWebSearchUserLocation(TypedDict):
    approximate: OpenAIWebSearchUserLocationApproximate
    type: Literal["approximate"]


class OpenAIWebSearchOptions(TypedDict, total=False):
    search_context_size: Optional[Literal["low", "medium", "high"]]
    user_location: Optional[OpenAIWebSearchUserLocation]


class AnthropicThinkingParam(TypedDict, total=False):
    type: Literal["enabled"]
    budget_tokens: int


InstructorModeParam = Literal[
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


class CompletionsSettings(TypedDict):
    """Accepted settings for the `litellm` completion function."""

    model: str
    messages: List
    timeout: Optional[Union[float, str, Timeout]]
    temperature: Optional[float]
    top_p: Optional[float]
    n: Optional[int]
    stream: Optional[bool]
    stream_options: Optional[Dict[str, Any]]
    stop: Optional[str]
    max_completion_tokens: Optional[int]
    max_tokens: Optional[int]
    modalities: Optional[List[ChatCompletionModality]]
    prediction: Optional[ChatCompletionPredictionContentParam]
    audio: Optional[ChatCompletionAudioParam]
    presence_penalty: Optional[float]
    frequency_penalty: Optional[float]
    logit_bias: Optional[Dict[str, float]]
    user: Optional[str]
    reasoning_effort: Optional[Literal["low", "medium", "high"]]
    # NOTE: response_format is not used within the `completions` resource
    # in place of `instructor` and the `type` parameter
    seed: Optional[int]
    tools: Optional[List]
    tool_choice: Optional[Union[str, Dict[str, Any]]]
    logprobs: Optional[bool]
    top_logprobs: Optional[int]
    parallel_tool_calls: Optional[bool]
    web_search_options: Optional[OpenAIWebSearchOptions]
    deployment_id: Optional[str]
    extra_headers: Optional[Dict[str, str]]
    base_url: Optional[str]
    functions: Optional[List]
    function_call: Optional[str]
    # set api_base, api_version, api_key
    api_version: Optional[str]
    api_key: Optional[str]
    model_list: Optional[list]
    # Optional liteLLM function params
    thinking: Optional[AnthropicThinkingParam]


class CompletionsError(Exception):
    """Error raised when an error occurs during a completion."""

    def __init__(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.args = args
        self.kwargs = kwargs


class CompletionsClient(Generic[CompletionsOutputType]):
    """Client for working with language model completions and structured
    outputs using the `litellm` and `instructor` libraries."""

    @staticmethod
    async def async_chat_completion(
        messages: CompletionsInputParam,
        instructions: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
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
    ):
        try:
            parsed_messages = parse_completions_input(messages, instructions)
        except Exception as e:
            raise CompletionsError(
                f"Error parsing completions input: {e}",
                input=messages,
            ) from e

        params: CompletionsSettings = {
            "model": model,
            "messages": parsed_messages,
            "timeout": timeout,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "max_completion_tokens": max_completion_tokens,
            "max_tokens": max_tokens,
            "modalities": modalities,
            "prediction": prediction,
            "audio": audio,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "reasoning_effort": reasoning_effort,
            "seed": seed,
            "tools": tools,
            "tool_choice": tool_choice,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "parallel_tool_calls": parallel_tool_calls,
            "web_search_options": web_search_options,
            "deployment_id": deployment_id,
            "extra_headers": extra_headers,
            "base_url": base_url,
            "functions": functions,
            "function_call": function_call,
            "api_version": api_version,
            "api_key": api_key,
            "model_list": model_list,
            "thinking": thinking,
        }

        if not stream:
            response = await get_litellm().acompletion(
                **{k: v for k, v in params.items() if v is not None}
            )
            return convert_response_to_completion(response)
        else:
            stream = await get_litellm().acompletion(
                **{k: v for k, v in params.items() if v is not None},
                stream=True,
                stream_options=stream_options if stream_options else None,
            )
            return create_async_completion_stream(stream, output_type=str, model=model)

    @staticmethod
    def chat_completion(
        messages: CompletionsInputParam,
        instructions: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
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
    ):
        try:
            parsed_messages = parse_completions_input(messages, instructions)
        except Exception as e:
            raise CompletionsError(
                f"Error parsing completions input: {e}",
                input=messages,
            ) from e

        params: CompletionsSettings = {
            "model": model,
            "messages": parsed_messages,
            "timeout": timeout,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "max_completion_tokens": max_completion_tokens,
            "max_tokens": max_tokens,
            "modalities": modalities,
            "prediction": prediction,
            "audio": audio,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "reasoning_effort": reasoning_effort,
            "seed": seed,
            "tools": tools,
            "tool_choice": tool_choice,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "parallel_tool_calls": parallel_tool_calls,
            "web_search_options": web_search_options,
            "deployment_id": deployment_id,
            "extra_headers": extra_headers,
            "base_url": base_url,
            "functions": functions,
            "function_call": function_call,
            "api_version": api_version,
            "api_key": api_key,
            "model_list": model_list,
            "thinking": thinking,
        }

        if not stream:
            response = get_litellm().completion(
                **{k: v for k, v in params.items() if v is not None}
            )
            return convert_response_to_completion(response)
        else:
            stream = get_litellm().completion(
                **{k: v for k, v in params.items() if v is not None},
                stream=True,
                stream_options=stream_options if stream_options else None,
            )
            return create_completion_stream(stream, output_type=str, model=model)

    @staticmethod
    async def async_structured_output(
        messages: CompletionsInputParam,
        instructions: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        type: CompletionsOutputType = str,
        instructor_mode: InstructorModeParam = "tool_call",
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
    ):
        try:
            parsed_messages = parse_completions_input(messages, instructions)
        except Exception as e:
            raise CompletionsError(
                f"Error parsing completions input: {e}",
                input=messages,
            ) from e

        parsed_messages = format_tool_calls(parsed_messages)

        params: CompletionsSettings = {
            "model": model,
            "messages": parsed_messages,
            "timeout": timeout,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "max_completion_tokens": max_completion_tokens,
            "max_tokens": max_tokens,
            "modalities": modalities,
            "prediction": prediction,
            "audio": audio,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "reasoning_effort": reasoning_effort,
            "seed": seed,
            "tools": tools,
            "tool_choice": tool_choice,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "parallel_tool_calls": parallel_tool_calls,
            "web_search_options": web_search_options,
            "deployment_id": deployment_id,
            "extra_headers": extra_headers,
            "base_url": base_url,
            "functions": functions,
            "function_call": function_call,
            "api_version": api_version,
            "api_key": api_key,
            "model_list": model_list,
            "thinking": thinking,
        }

        if type is str:
            return await CompletionsClient.async_chat_completion(
                messages=messages,
                instructions=instructions,
                model=model,
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

        try:
            client = get_instructor().from_litellm(
                completion=get_litellm().acompletion,
                mode=get_instructor().Mode(instructor_mode),
            )
        except Exception as e:
            raise CompletionsError(
                f"Error creating instructor client: {e}",
                input=messages,
            ) from e

        if not is_pydantic_basemodel(type):
            response_model = convert_to_pydantic_model(
                target=type,
                name="Response",
                field_name="value",
                description="A single field response in the correct type.",
            )
        else:
            response_model = type

        if stream:
            stream = await client.chat.completions.create_partial(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )
            return create_async_completion_stream(stream, output_type=type, model=model)
        else:
            response = await client.chat.completions.create(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )

            # Extract the actual value if using converted pydantic model
            if not is_pydantic_basemodel(type) and hasattr(response, "value"):
                actual_output = response.value
            else:
                actual_output = response

            return Completion(
                output=actual_output, model=model, content=None, completion=None
            )

    @staticmethod
    def structured_output(
        messages: CompletionsInputParam,
        instructions: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        type: CompletionsOutputType = str,
        instructor_mode: InstructorModeParam = "tool_call",
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
    ):
        try:
            parsed_messages = parse_completions_input(messages, instructions)
        except Exception as e:
            raise CompletionsError(
                f"Error parsing completions input: {e}",
                input=messages,
            ) from e

        parsed_messages = format_tool_calls(parsed_messages)

        params: CompletionsSettings = {
            "model": model,
            "messages": parsed_messages,
            "timeout": timeout,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "max_completion_tokens": max_completion_tokens,
            "max_tokens": max_tokens,
            "modalities": modalities,
            "prediction": prediction,
            "audio": audio,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "reasoning_effort": reasoning_effort,
            "seed": seed,
            "tools": tools,
            "tool_choice": tool_choice,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "parallel_tool_calls": parallel_tool_calls,
            "web_search_options": web_search_options,
            "deployment_id": deployment_id,
            "extra_headers": extra_headers,
            "base_url": base_url,
            "functions": functions,
            "function_call": function_call,
            "api_version": api_version,
            "api_key": api_key,
            "model_list": model_list,
            "thinking": thinking,
        }

        if type is str:
            return CompletionsClient.chat_completion(
                messages=messages,
                instructions=instructions,
                model=model,
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

        try:
            client = get_instructor().from_litellm(
                completion=get_litellm().completion,
                mode=get_instructor().Mode(instructor_mode),
            )
        except Exception as e:
            raise CompletionsError(
                f"Error creating instructor client: {e}",
                input=messages,
            ) from e

        if not is_pydantic_basemodel(type):
            response_model = convert_to_pydantic_model(
                target=type,
                name="Response",
                field_name="value",
                description="A single field response in the correct type.",
            )
        else:
            response_model = type

        if stream:
            stream = client.chat.completions.create_partial(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )
            return create_completion_stream(stream, output_type=type, model=model)
        else:
            response = client.chat.completions.create(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )

            # Extract the actual value if using converted pydantic model
            if not is_pydantic_basemodel(type) and hasattr(response, "value"):
                actual_output = response.value
            else:
                actual_output = response

            return Completion(
                output=actual_output, model=model, content=None, completion=None
            )
