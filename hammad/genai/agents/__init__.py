"""hammad.genai.agents"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from .agent import (
        Agent,
        create_agent,
    )
    from .run import run_agent, run_agent_iter, async_run_agent, async_run_agent_iter

    # Types
    from .types.agent_context import AgentContext
    from .types.agent_event import AgentEvent
    from .types.agent_hooks import HookManager, HookDecorator
    from .types.agent_messages import AgentMessages
    from .types.agent_response import (
        AgentResponse,
        _create_agent_response_from_language_model_response,
    )
    from .types.agent_stream import AgentStream, AgentResponseChunk


__all__ = [
    # hammad.genai.agents.agent
    "Agent",
    "create_agent",
    # hammad.genai.agents.run
    "run_agent",
    "run_agent_iter",
    "async_run_agent",
    "async_run_agent_iter",
    # hammad.genai.agents.types.agent_context
    "AgentContext",
    # hammad.genai.agents.types.agent_event
    "AgentEvent",
    # hammad.genai.agents.types.agent_hooks
    "HookManager",
    "HookDecorator",
    # hammad.genai.agents.types.agent_messages
    "AgentMessages",
    # hammad.genai.agents.types.agent_response
    "AgentResponse",
    "_create_agent_response_from_language_model_response",
    # hammad.genai.agents.types.agent_stream
    "AgentStream",
    "AgentResponseChunk",
]


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return __all__
