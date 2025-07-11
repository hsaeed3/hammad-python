"""hammad.genai.language_models.language_model_settings"""

from typing import (
    Any,
    Dict,
    List,
    Union,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Callable,
    Optional,
)
import sys
from pydantic import BaseModel, Field

if sys.version_info >= (3, 12):
    from typing import TypedDict, Required, NotRequired
else:
    from typing_extensions import TypedDict, Required, NotRequired

if TYPE_CHECKING:
    pass

from .language_model_name import LanguageModelName
from .language_model_instructor_mode import LanguageModelInstructorMode
from ....types.base import BaseGenAIModelSettings

__all__ = [
    "LanguageModelSettings",
    "LanguageModelProviderSettings",
]


T = TypeVar("T")


class LanguageModelSettings(BaseGenAIModelSettings):
    """Complete settings for language model requests."""

    # Structured output settings
    type: Optional[Type[T]] = None
    instructor_mode: Optional[LanguageModelInstructorMode] = None
    response_field_name: Optional[str] = None
    response_field_instruction: Optional[str] = None
    max_retries: Optional[int] = None
    strict: Optional[bool] = None
    validation_context: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

    # Tool settings
    tools: Optional[List[Any]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    parallel_tool_calls: Optional[bool] = None
    functions: Optional[List[Any]] = None
    function_call: Optional[str] = None

    # Streaming settings
    stream: Optional[bool] = None
    stream_options: Optional[Dict[str, Any]] = None

    # Hook settings
    completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None
    completion_response_hooks: Optional[List[Callable[..., None]]] = None
    completion_error_hooks: Optional[List[Callable[..., None]]] = None
    completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None
    parse_error_hooks: Optional[List[Callable[..., None]]] = None

    # Extended settings
    timeout: Optional[Union[float, str]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stop: Optional[str] = None
    max_completion_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    modalities: Optional[List[Any]] = None
    prediction: Optional[Any] = None
    audio: Optional[Any] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    reasoning_effort: Optional[str] = None
    seed: Optional[int] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    thinking: Optional[Dict[str, Any]] = None
    web_search_options: Optional[Dict[str, Any]] = None
