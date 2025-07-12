"""hammad.genai.graphs.plugins - Plugin system for graphs"""

from typing import Any, Dict, List, Optional, Type, Callable, Union
from dataclasses import dataclass, field

from ..types.history import History
from ..models.language.model import LanguageModel
from ..models.language.types.language_model_name import LanguageModelName
from .types import BasePlugin, GraphContext

__all__ = [
    "plugin",
    "PluginDecorator",
    "HistoryPlugin",
    "MemoryPlugin",
    "AudioPlugin",
    "ServePlugin",
    "SettingsPlugin",
]


@dataclass
class PluginConfig:
    """Configuration for a plugin."""

    name: str
    plugin_class: Type[BasePlugin]
    config: Dict[str, Any] = field(default_factory=dict)


class PluginDecorator:
    """Decorator for adding plugins to graphs."""

    def __init__(self):
        self._plugins: List[PluginConfig] = []

    def history(
        self,
        summarize: bool = False,
        model: Optional[LanguageModelName] = None,
        max_messages: int = 100,
        **kwargs: Any,
    ) -> Callable:
        """Add history plugin with automatic summarization."""

        def decorator(cls):
            self._plugins.append(
                PluginConfig(
                    name="history",
                    plugin_class=HistoryPlugin,
                    config={
                        "summarize": summarize,
                        "model": model,
                        "max_messages": max_messages,
                        **kwargs,
                    },
                )
            )
            return cls

        return decorator

    def memory(
        self,
        collection_name: Optional[str] = None,
        searchable: bool = True,
        vector_enabled: bool = True,
        **kwargs: Any,
    ) -> Callable:
        """Add memory plugin for long-term searchable memory."""

        def decorator(cls):
            self._plugins.append(
                PluginConfig(
                    name="memory",
                    plugin_class=MemoryPlugin,
                    config={
                        "collection_name": collection_name,
                        "searchable": searchable,
                        "vector_enabled": vector_enabled,
                        **kwargs,
                    },
                )
            )
            return cls

        return decorator

    def audio(self, model: LanguageModelName, **kwargs: Any) -> Callable:
        """Add audio plugin for voice output."""

        def decorator(cls):
            self._plugins.append(
                PluginConfig(
                    name="audio",
                    plugin_class=AudioPlugin,
                    config={"model": model, **kwargs},
                )
            )
            return cls

        return decorator

    def serve(
        self,
        server_type: Union[str, List[str]] = "http",
        settings: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Callable:
        """Add serve plugin for running graphs as servers."""

        def decorator(cls):
            self._plugins.append(
                PluginConfig(
                    name="serve",
                    plugin_class=ServePlugin,
                    config={
                        "server_type": server_type,
                        "settings": settings or {},
                        **kwargs,
                    },
                )
            )
            return cls

        return decorator

    def settings(
        self,
        model: Optional[LanguageModelName] = None,
        tools: Optional[List[Callable]] = None,
        summarize_tools: bool = True,
        summarize_tools_with_model: bool = False,
        max_steps: Optional[int] = None,
        **kwargs: Any,
    ) -> Callable:
        """Add settings plugin for global configuration."""

        def decorator(cls):
            self._plugins.append(
                PluginConfig(
                    name="settings",
                    plugin_class=SettingsPlugin,
                    config={
                        "model": model,
                        "tools": tools or [],
                        "summarize_tools": summarize_tools,
                        "summarize_tools_with_model": summarize_tools_with_model,
                        "max_steps": max_steps,
                        **kwargs,
                    },
                )
            )
            return cls

        return decorator

    def get_plugins(self) -> List[PluginConfig]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()


# Plugin implementations


class HistoryPlugin(BasePlugin):
    """Plugin for managing graph history with optional summarization."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history: Optional[History] = None
        self.summarize = kwargs.get("summarize", False)
        self.model = kwargs.get("model")
        self.max_messages = kwargs.get("max_messages", 100)

    def on_action_start(self, context: GraphContext[Any], action_name: str) -> None:
        """Handle action start events."""
        if self.history is None:
            self.history = History()

        # Add event to history
        self.history.add_message(
            {
                "role": "system",
                "content": f"Graph action started: {action_name}",
                "metadata": {"action_name": action_name, "event_type": "action_start"},
            }
        )

    def on_action_end(
        self, context: GraphContext[Any], action_name: str, result: Any
    ) -> None:
        """Handle action end events."""
        if self.history is None:
            self.history = History()

        # Add event to history
        self.history.add_message(
            {
                "role": "system",
                "content": f"Graph action completed: {action_name}",
                "metadata": {
                    "action_name": action_name,
                    "result": result,
                    "event_type": "action_end",
                },
            }
        )

        # Summarize if needed
        if self.summarize and len(self.history.messages) >= self.max_messages:
            self._summarize_history()

    def _summarize_history(self):
        """Summarize the history using the configured model."""
        if self.model and self.history:
            # This would use the language model to summarize
            # For now, just truncate
            self.history.messages = self.history.messages[-self.max_messages // 2 :]


class MemoryPlugin(BasePlugin):
    """Plugin for long-term memory storage and retrieval."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collection_name = kwargs.get("collection_name", "graph_memory")
        self.searchable = kwargs.get("searchable", True)
        self.vector_enabled = kwargs.get("vector_enabled", True)
        self.memory_store: Dict[str, Any] = {}

    def on_action_end(
        self, context: GraphContext[Any], action_name: str, result: Any
    ) -> None:
        """Store action results in memory."""
        memory_key = f"{action_name}_{len(self.memory_store)}"
        self.memory_store[memory_key] = {
            "action_name": action_name,
            "result": result,
            "timestamp": context.metadata.get("timestamp"),
            "state": context.state,
        }

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory for relevant information."""
        # Simple text search for now
        results = []
        for key, value in self.memory_store.items():
            if query.lower() in str(value).lower():
                results.append(value)
        return results


class AudioPlugin(BasePlugin):
    """Plugin for audio/TTS output."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model")

    def on_action_end(
        self, context: GraphContext[Any], action_name: str, result: Any
    ) -> None:
        """Generate audio for action results."""
        if self.model and result:
            # This would generate audio using TTS
            context.metadata["audio_generated"] = True
            context.metadata["tts_model"] = self.model
            context.metadata["audio_content"] = str(result)


class ServePlugin(BasePlugin):
    """Plugin for serving graphs as web services."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_type = kwargs.get("server_type", "http")
        self.settings = kwargs.get("settings", {})

    def on_graph_start(self, context: GraphContext[Any]) -> None:
        """Handle graph start for server setup."""
        context.metadata["server_type"] = self.server_type
        context.metadata["serve_enabled"] = True

    def on_graph_end(self, context: GraphContext[Any]) -> None:
        """Handle graph end for server response."""
        context.metadata["server_response_ready"] = True


class SettingsPlugin(BasePlugin):
    """Plugin for global graph settings."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model")
        self.tools = kwargs.get("tools", [])
        self.summarize_tools = kwargs.get("summarize_tools", True)
        self.summarize_tools_with_model = kwargs.get(
            "summarize_tools_with_model", False
        )
        self.max_steps = kwargs.get("max_steps")

    def on_graph_start(self, context: GraphContext[Any]) -> None:
        """Apply global settings at graph start."""
        context.metadata["global_model"] = self.model
        context.metadata["global_tools"] = self.tools
        context.metadata["max_steps"] = self.max_steps
        context.metadata["summarize_tools"] = self.summarize_tools


# Global plugin decorator instance
plugin = PluginDecorator()
