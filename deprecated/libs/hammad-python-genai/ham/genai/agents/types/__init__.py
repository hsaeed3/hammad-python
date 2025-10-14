"""ham.genai.agents.types"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ....core._internal import type_checking_importer  # type: ignore


if TYPE_CHECKING:
    from .agent_event import AgentEvent
    from .agent_hooks import HookManager, HookDecorator
    from .agent_response import (
        AgentResponse,
        _create_agent_response_from_language_model_response,
    )
    from .agent_stream import AgentStream, AgentResponseChunk
    from .agent_context import AgentContext
    from .agent_messages import AgentMessages


__all__ = [
    # hammad.genai.agents.types.agent_event
    "AgentEvent",
    # hammad.genai.agents.types.agent_hooks
    "HookManager",
    "HookDecorator",
    # hammad.genai.agents.types.agent_response
    "AgentResponse",
    "_create_agent_response_from_language_model_response",
    # hammad.genai.agents.types.agent_stream
    "AgentStream",
    "AgentResponseChunk",
    # hammad.genai.agents.types.agent_context
    "AgentContext",
    # hammad.genai.agents.types.agent_messages
    "AgentMessages",
]


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return __all__
