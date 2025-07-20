"""hammad.genai.agents.types.agent_context"""

from typing import Dict, Any, TypeVar
from pydantic import BaseModel


__all__ = [
    "AgentContext",
]


AgentContext = TypeVar("AgentContext", bound=BaseModel | Dict[str, Any])
"""A context object that can be used to store information about the agent's state."""
