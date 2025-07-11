"""hammad.genai.models.language.types.language_model_messages"""

from typing import (
    TypeAlias,
    Union,
    Any,
    List,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletionMessageParam,
    )


__all__ = [
    "LanguageModelMessages",
]


LanguageModelMessages: TypeAlias = Union[
    str,
    "ChatCompletionMessageParam",
    "List[ChatCompletionMessageParam]",
    Any,
]
"""Type alias for the input parameters of a language model request."""
