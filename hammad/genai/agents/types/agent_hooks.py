"""hammad.genai.agents.types.agent_hooks"""

from typing import Any, Dict, List, Callable, Optional
from .agent_event import AgentEvent


__all__ = [
    "HookManager",
    "HookDecorator",
]


class HookManager:
    """Manages hooks for agent events."""

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.specific_hooks: Dict[str, Dict[str, List[Callable]]] = {}

    def register_hook(
        self, event_type: str, callback: Callable, specific_name: Optional[str] = None
    ):
        """Register a hook for an event type.

        Args:
            event_type: The type of event to hook into
            callback: The callback function to execute
            specific_name: Optional specific name for targeted hooks
        """
        if specific_name:
            if event_type not in self.specific_hooks:
                self.specific_hooks[event_type] = {}
            if specific_name not in self.specific_hooks[event_type]:
                self.specific_hooks[event_type][specific_name] = []
            self.specific_hooks[event_type][specific_name].append(callback)
        else:
            if event_type not in self.hooks:
                self.hooks[event_type] = []
            self.hooks[event_type].append(callback)

    def trigger_hooks(
        self, event_type: str, data: Any, specific_name: Optional[str] = None
    ) -> Any:
        """Trigger hooks for an event type.

        Args:
            event_type: The type of event
            data: The event data
            specific_name: Optional specific name for targeted hooks

        Returns:
            The potentially modified data after running through hooks
        """
        result = data

        # Trigger general hooks
        if event_type in self.hooks:
            for hook in self.hooks[event_type]:
                hook_result = hook(result)
                if hook_result is not None:
                    result = hook_result

        # Trigger specific hooks
        if specific_name and event_type in self.specific_hooks:
            if specific_name in self.specific_hooks[event_type]:
                for hook in self.specific_hooks[event_type][specific_name]:
                    hook_result = hook(result)
                    if hook_result is not None:
                        result = hook_result

        return result

    def trigger_event(
        self, event: AgentEvent, specific_name: Optional[str] = None
    ) -> Any:
        """Trigger hooks for an AgentEvent.

        Args:
            event: The AgentEvent instance
            specific_name: Optional specific name for targeted hooks

        Returns:
            The potentially modified event data after running through hooks
        """
        return self.trigger_hooks(event.event_type, event.output, specific_name)

    def clear_hooks(
        self, event_type: Optional[str] = None, specific_name: Optional[str] = None
    ):
        """Clear hooks for a specific event type or all hooks.

        Args:
            event_type: Optional event type to clear (clears all if None)
            specific_name: Optional specific name to clear
        """
        if event_type is None:
            self.hooks.clear()
            self.specific_hooks.clear()
        else:
            if event_type in self.hooks:
                if specific_name is None:
                    del self.hooks[event_type]

            if event_type in self.specific_hooks:
                if specific_name is None:
                    del self.specific_hooks[event_type]
                elif specific_name in self.specific_hooks[event_type]:
                    del self.specific_hooks[event_type][specific_name]

    def list_hooks(self) -> Dict[str, Any]:
        """List all registered hooks.

        Returns:
            Dictionary containing all hooks information
        """
        return {
            "general_hooks": {k: len(v) for k, v in self.hooks.items()},
            "specific_hooks": {
                k: {sk: len(sv) for sk, sv in v.items()}
                for k, v in self.specific_hooks.items()
            },
        }


class HookDecorator:
    """Provides type-hinted hook decorators with extensible event system."""

    def __init__(self, hook_manager: HookManager):
        self.hook_manager = hook_manager
        self._event_types = set()

    def __call__(self, event_type: str, specific_name: Optional[str] = None):
        """Register a hook for any event type.

        Args:
            event_type: The type of event to hook into
            specific_name: Optional specific name for targeted hooks

        Returns:
            Decorator function
        """

        def decorator(func: Callable):
            self.hook_manager.register_hook(event_type, func, specific_name)
            self._event_types.add(event_type)
            return func

        return decorator

    def get_registered_event_types(self) -> set:
        """Get all registered event types."""
        return self._event_types.copy()

    def supports_event(self, event_type: str) -> bool:
        """Check if an event type is supported."""
        return event_type in self._event_types

    # Convenience decorators for common events
    def on_context_update(self, specific_name: Optional[str] = None):
        """Decorator for context update events."""
        return self.__call__("context_update", specific_name)

    def on_tool_call(self, specific_name: Optional[str] = None):
        """Decorator for tool call events."""
        return self.__call__("tool_call", specific_name)

    def on_tool_execution(self, specific_name: Optional[str] = None):
        """Decorator for tool execution events."""
        return self.__call__("tool_execution", specific_name)

    def on_tool_response(self, specific_name: Optional[str] = None):
        """Decorator for tool response events."""
        return self.__call__("tool_response", specific_name)

    def on_final_response(self, specific_name: Optional[str] = None):
        """Decorator for final response events."""
        return self.__call__("final_response", specific_name)

    def on_step_start(self, specific_name: Optional[str] = None):
        """Decorator for step start events."""
        return self.__call__("step_start", specific_name)

    def on_step_end(self, specific_name: Optional[str] = None):
        """Decorator for step end events."""
        return self.__call__("step_end", specific_name)

    def on_error(self, specific_name: Optional[str] = None):
        """Decorator for error events."""
        return self.__call__("error", specific_name)

    def on_stream_chunk(self, specific_name: Optional[str] = None):
        """Decorator for stream chunk events."""
        return self.__call__("stream_chunk", specific_name)

    # Dynamic event type classes - these are created dynamically
    # based on the actual events that occur in the system
    def __getattr__(self, name: str):
        """Dynamically create event type classes for better type hinting."""
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # Create a dynamic class for this event type
        class DynamicEventType:
            def __init__(
                self, event_data: Any = None, metadata: Optional[Dict[str, Any]] = None
            ):
                self.event_data = event_data
                self.metadata = metadata or {}

            def __repr__(self):
                return f"{name}(data={self.event_data}, metadata={self.metadata})"

        DynamicEventType.__name__ = name
        DynamicEventType.__qualname__ = f"{self.__class__.__name__}.{name}"

        # Cache the class
        setattr(self, name, DynamicEventType)
        return DynamicEventType
