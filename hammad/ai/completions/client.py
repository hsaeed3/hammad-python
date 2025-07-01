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

from ...data.models.pydantic.converters import convert_to_pydantic_model
from .._utils import get_litellm, get_instructor
from ...typing import is_pydantic_basemodel
from .utils import (
    format_tool_calls,
    parse_completions_input,
    convert_response_to_completion,
    create_async_completion_stream,
    create_completion_stream,
    InstructorStreamWrapper,
    AsyncInstructorStreamWrapper,
)
from .settings import (
    CompletionsSettings,
    OpenAIWebSearchOptions,
    AnthropicThinkingParam,
)
from .types import (
    CompletionsInstructorModeParam,
    CompletionsInputParam,
    CompletionsOutputType,
    Completion,
)


__all__ = "CompletionsClient"


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
                field_name=response_field_name,
                description=response_field_instruction,
            )
        else:
            response_model = type

        if stream:
            # Create wrapper to capture raw content via hooks
            wrapper = AsyncInstructorStreamWrapper(
                client=client,
                response_model=response_model,
                params={
                    "max_retries": max_retries,
                    "strict": strict,
                    **{k: v for k, v in params.items() if v is not None},
                },
                output_type=type,
                model=model,
            )
            return create_async_completion_stream(
                wrapper, output_type=type, model=model
            )
        else:
            response, completion = await client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )

            # Extract the actual value if using converted pydantic model
            if not is_pydantic_basemodel(type) and hasattr(
                response, response_field_name
            ):
                actual_output = getattr(response, response_field_name)
            else:
                actual_output = response

            # Extract content and tool calls from the completion
            content = None
            tool_calls = None
            if hasattr(completion, "choices") and completion.choices:
                choice = completion.choices[0]
                if hasattr(choice, "message"):
                    message = choice.message
                    content = getattr(message, "content", None)
                    tool_calls = getattr(message, "tool_calls", None)

            return Completion(
                output=actual_output,
                model=model,
                content=content,
                tool_calls=tool_calls,
                completion=completion,
            )

    @staticmethod
    def structured_output(
        messages: CompletionsInputParam,
        instructions: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
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
                field_name=response_field_name,
                description=response_field_instruction,
            )
        else:
            response_model = type

        if stream:
            # Create wrapper to capture raw content via hooks
            wrapper = InstructorStreamWrapper(
                client=client,
                response_model=response_model,
                params={
                    "max_retries": max_retries,
                    "strict": strict,
                    **{k: v for k, v in params.items() if v is not None},
                },
                output_type=type,
                model=model,
            )
            return create_completion_stream(wrapper, output_type=type, model=model)
        else:
            response, completion = client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=max_retries,
                strict=strict,
                **{k: v for k, v in params.items() if v is not None},
            )

            # Extract the actual value if using converted pydantic model
            if not is_pydantic_basemodel(type) and hasattr(
                response, response_field_name
            ):
                actual_output = getattr(response, response_field_name)
            else:
                actual_output = response

            # Extract content and tool calls from the completion
            content = None
            tool_calls = None
            if hasattr(completion, "choices") and completion.choices:
                choice = completion.choices[0]
                if hasattr(choice, "message"):
                    message = choice.message
                    content = getattr(message, "content", None)
                    tool_calls = getattr(message, "tool_calls", None)

            return Completion(
                output=actual_output,
                model=model,
                content=content,
                tool_calls=tool_calls,
                completion=completion,
            )
