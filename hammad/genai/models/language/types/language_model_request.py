"""hammad.genai.language_models.language_model_request"""

from typing import (
    Any,
    Dict,
    List,
    Union,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Callable,
)
import sys

if sys.version_info >= (3, 12):
    from typing import TypedDict, Required, NotRequired
else:
    from typing_extensions import TypedDict, Required, NotRequired

if TYPE_CHECKING:
    from httpx import Timeout
    from openai.types.chat import (
        ChatCompletionModality,
        ChatCompletionPredictionContentParam,
        ChatCompletionAudioParam,
    )

from .language_model_name import LanguageModelName
from .language_model_instructor_mode import LanguageModelInstructorMode

__all__ = [
    "LanguageModelRequest",
]


T = TypeVar("T")


class LanguageModelRequestProviderSettings(TypedDict, total=False):
    """Provider-specific settings for language model requests."""

    model: Required[LanguageModelName]
    base_url: NotRequired[str]
    api_key: NotRequired[str]
    api_version: NotRequired[str]
    organization: NotRequired[str]
    deployment_id: NotRequired[str]
    model_list: NotRequired[List[Any]]
    extra_headers: NotRequired[Dict[str, str]]


class LanguageModelRequestStructuredOutputSettings(TypedDict, total=False):
    """Settings for structured output generation."""

    type: Required[Type[T]]
    instructor_mode: NotRequired[LanguageModelInstructorMode]
    response_field_name: NotRequired[str]
    response_field_instruction: NotRequired[str]
    max_retries: NotRequired[int]
    strict: NotRequired[bool]
    validation_context: NotRequired[Dict[str, Any]]
    context: NotRequired[Dict[str, Any]]


class LanguageModelRequestToolsSettings(TypedDict, total=False):
    """Settings for tool usage in language model requests."""

    tools: NotRequired[List[Any]]
    tool_choice: NotRequired[Union[str, Dict[str, Any]]]
    parallel_tool_calls: NotRequired[bool]
    functions: NotRequired[List[Any]]
    function_call: NotRequired[str]


class LanguageModelRequestStreamingSettings(TypedDict, total=False):
    """Settings for streaming responses."""

    stream: Required[bool]
    stream_options: NotRequired[Dict[str, Any]]


class LanguageModelRequestHooksSettings(TypedDict, total=False):
    """Settings for instructor hooks."""

    completion_kwargs_hooks: NotRequired[List[Callable[..., None]]]
    completion_response_hooks: NotRequired[List[Callable[..., None]]]
    completion_error_hooks: NotRequired[List[Callable[..., None]]]
    completion_last_attempt_hooks: NotRequired[List[Callable[..., None]]]
    parse_error_hooks: NotRequired[List[Callable[..., None]]]


class LanguageModelRequestExtendedSettings(TypedDict, total=False):
    """Extended settings for language model requests."""

    timeout: NotRequired[Union[float, str, "Timeout"]]
    temperature: NotRequired[float]
    top_p: NotRequired[float]
    n: NotRequired[int]
    stop: NotRequired[str]
    max_completion_tokens: NotRequired[int]
    max_tokens: NotRequired[int]
    modalities: NotRequired[List["ChatCompletionModality"]]
    prediction: NotRequired["ChatCompletionPredictionContentParam"]
    audio: NotRequired["ChatCompletionAudioParam"]
    presence_penalty: NotRequired[float]
    frequency_penalty: NotRequired[float]
    logit_bias: NotRequired[Dict[str, float]]
    user: NotRequired[str]
    reasoning_effort: NotRequired[str]
    seed: NotRequired[int]
    logprobs: NotRequired[bool]
    top_logprobs: NotRequired[int]
    thinking: NotRequired[Dict[str, Any]]
    web_search_options: NotRequired[Dict[str, Any]]


class LanguageModelRequest(
    LanguageModelRequestProviderSettings,
    LanguageModelRequestStructuredOutputSettings,
    LanguageModelRequestToolsSettings,
    LanguageModelRequestStreamingSettings,
    LanguageModelRequestHooksSettings,
    LanguageModelRequestExtendedSettings,
):
    """Complete settings for language model requests."""

    pass
