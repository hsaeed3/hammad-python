"""hammad.genai.agents.types.agent_messages"""

from typing import TypeAlias, Union, List, Any, TYPE_CHECKING

from ...models.language.types import LanguageModelMessages

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam
    from ...types.history import History


__all__ = [
    "AgentMessages",
]


AgentMessages: TypeAlias = Union[
    str,
    "ChatCompletionMessageParam",
    "List[ChatCompletionMessageParam]",
    "History",
    LanguageModelMessages,
    Any,
]
"""Type alias for agent message inputs that extends LanguageModelMessages to include History objects.

This type alias allows agents to accept:
- All standard LanguageModelMessages types (str, ChatCompletionMessageParam, List[ChatCompletionMessageParam])
- History objects for conversation history management
- Any other type for flexibility
"""
