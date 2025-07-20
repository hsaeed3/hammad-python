"""hammad.genai.agents.types.agent_event"""

from typing import Any, Dict, Optional, Literal
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionContentPartParam

from ...types.base import BaseGenAIModelEvent


__all__ = [
    "AgentEvent",
]


class AgentEvent(BaseGenAIModelEvent[Any]):
    """Base class for all agent events with universal event checking.

    This class extends BaseGenAIModelEvent to provide agent-specific
    event handling capabilities.
    """

    type: Literal["agent"] = "agent"
    """The type of the model. Always 'agent'."""

    model: str = "agent"
    """The model that generated this event."""

    output: Any = None
    """The event data/output."""

    event_type: str
    """The specific type of event (e.g., 'context_update', 'tool_call', etc.)."""

    metadata: Dict[str, Any] = {}
    """Additional metadata for the event."""

    def __init__(
        self,
        event_type: str,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Initialize an AgentEvent.

        Args:
            event_type: The type of event
            data: The event data
            metadata: Additional metadata
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            output=data, event_type=event_type, metadata=metadata or {}, **kwargs
        )

    def is_event(self, event_type: str) -> bool:
        """Universal event type checker."""
        return self.event_type == event_type

    def is_event_category(self, category: str) -> bool:
        """Check if event belongs to a category (e.g., 'tool' matches 'tool_call', 'tool_execution')."""
        return self.event_type.startswith(category)

    def has_metadata(self, key: str) -> bool:
        """Check if event has specific metadata."""
        return key in self.metadata

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    # Common event type checks (for convenience)
    def is_context_update(self) -> bool:
        return self.is_event("context_update")

    def is_tool_call(self) -> bool:
        return self.is_event("tool_call")

    def is_tool_execution(self) -> bool:
        return self.is_event("tool_execution")

    def is_tool_response(self) -> bool:
        return self.is_event("tool_response")

    def is_final_response(self) -> bool:
        return self.is_event("final_response")

    def is_step_start(self) -> bool:
        return self.is_event("step_start")

    def is_step_end(self) -> bool:
        return self.is_event("step_end")

    def is_error(self) -> bool:
        return self.is_event("error")

    def is_stream_chunk(self) -> bool:
        return self.is_event("stream_chunk")

    # Category checks
    def is_tool_event(self) -> bool:
        return self.is_event_category("tool")

    def is_context_event(self) -> bool:
        return self.is_event_category("context")

    def is_stream_event(self) -> bool:
        return self.is_event_category("stream")

    def to_message(self) -> ChatCompletionMessageParam:
        """Convert the event to a chat completion message."""
        content = f"Event: {self.event_type}"
        if self.output:
            content += f"\nData: {self.output}"
        if self.metadata:
            content += f"\nMetadata: {self.metadata}"

        return {"role": "assistant", "content": content}

    def to_content_part(self) -> ChatCompletionContentPartParam:
        """Convert the event to a chat completion content part."""
        content = f"Event: {self.event_type}"
        if self.output:
            content += f" - {self.output}"

        return {"type": "text", "text": content}

    def __repr__(self) -> str:
        return f"AgentEvent(type='{self.event_type}', data={self.output}, metadata={self.metadata})"
