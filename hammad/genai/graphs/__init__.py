"""hammad.genai.graphs - Graph-based workflow framework built on pydantic-graph

This module provides a high-level interface for creating graph-based workflows
that integrate seamlessly with hammad's Agent and LanguageModel infrastructure.

Key Features:
- Action decorator system for defining graph nodes
- Automatic integration with Agent and LanguageModel
- IDE-friendly type hints and parameter unpacking
- Plugin system for extensibility
- Built on pydantic-graph for robust execution

Basic Usage:
    from hammad.genai.graphs import BaseGraph, action
    from pydantic import BaseModel

    class MyState(BaseModel):
        count: int = 0

    class CountingGraph(BaseGraph[MyState, str]):
        @action.start()
        def start_counting(self, ctx, agent, target: int):
            # Use agent for AI operations
            response = agent.run(f"Count from 1 to {target}")
            return response.output

    # Usage
    graph = CountingGraph()
    result = graph.run(target=5)
    print(result.output)

Advanced Usage with Plugins:
    from hammad.genai.graphs import plugin

    @plugin.history(summarize=True)
    @plugin.memory(collection_name="counting")
    class AdvancedGraph(BaseGraph[MyState, str]):
        @action.start(instructions="You are a helpful counting assistant")
        def count_with_memory(self, ctx, agent, target: int):
            # Agent will have instructions and plugins automatically applied
            return agent.run(f"Count to {target} and remember this session")
"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from .base import BaseGraph, action, ActionNode, GraphBuilder
    from .types import (
        GraphContext,
        GraphResponse,
        GraphState,
        BasePlugin,
        ActionSettings,
        ActionInfo,
        GraphEvent,
        GraphHistoryEntry,
        GraphStream,
        GraphResponseChunk,
        GraphNode,
        GraphEnd,
        PydanticGraphContext,
    )
    from .plugins import (
        plugin,
        PluginDecorator,
        HistoryPlugin,
        MemoryPlugin,
        AudioPlugin,
        ServePlugin,
        SettingsPlugin,
    )


__all__ = (
    # Core graph classes
    "BaseGraph",
    "GraphBuilder",
    # Action system
    "action",
    "ActionNode",
    "ActionSettings",
    "ActionInfo",
    # Plugin system
    "plugin",
    "BasePlugin",
    "PluginDecorator",
    "HistoryPlugin",
    "MemoryPlugin",
    "AudioPlugin",
    "ServePlugin",
    "SettingsPlugin",
    # Types and context
    "GraphContext",
    "GraphResponse",
    "GraphState",
    "GraphEvent",
    "GraphHistoryEntry",
    "GraphStream",
    "GraphResponseChunk",
    # Re-exports from pydantic-graph
    "GraphNode",
    "GraphEnd",
    "PydanticGraphContext",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
