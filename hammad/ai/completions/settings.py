"""hammad.ai.completions.settings"""

from typing import Any, Dict, List, Literal, Optional, Union
import sys
from httpx import Timeout

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

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


__all__ = (
    "CompletionsModelSettings",
    "CompletionsSettings",
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


class CompletionsModelSettings(TypedDict, total=False):
    """Accepted **MODEL** specific settings for the `litellm` completion function."""

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


class CompletionsSettings(CompletionsModelSettings, total=False):
    """Accepted settings for the `litellm` completion function."""

    model: str
    messages: List
