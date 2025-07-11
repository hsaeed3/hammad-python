"""hammad.genai.agents"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from .base.base_agent import BaseAgent
    from .base.base_agent_response import BaseAgentResponse
    from .base._streaming import (
        BaseAgentStream,
        BaseAgentAsyncStream,
        BaseAgentResponseChunk
    )

    # TYPES
    from .types.tool import (
        Tool,
        function_tool
    )
    from .types.history import (
        History
    )


__all__ = [
    # hammad.genai.agents.base
    "BaseAgent",
    "BaseAgentResponse",
    "BaseAgentStream",
    "BaseAgentAsyncStream",
    "BaseAgentResponseChunk",

    # hammad.genai.agents.types
    "Tool",
    "function_tool",
    "History"
]


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return __all__