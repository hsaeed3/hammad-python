"""hammad.genai.graphs.types - Types for the graph framework built on pydantic-graph"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
    Generic,
    Union,
    Callable,
    Iterator,
    AsyncIterator,
    TYPE_CHECKING,
)
from typing_extensions import Literal
from dataclasses import dataclass, field

# Import from pydantic-graph
from pydantic_graph import BaseNode, End, GraphRunContext, Graph as PydanticGraph
from pydantic import BaseModel, Field

from ...cache import cached
from ...typing import get_type_description
from ..agents.types.agent_response import AgentResponse
from ..models.language.types.language_model_response import LanguageModelResponse
from ..models.language.types.language_model_name import LanguageModelName
from ..types.history import History
from ..types.base import BaseGenAIModelStream

if TYPE_CHECKING:
    from .base import BaseGraph

__all__ = [
    "GraphState",
    "GraphContext",
    "GraphResponse",
    "GraphStream",
    "GraphResponseChunk",
    "ActionSettings",
    "ActionInfo",
    "GraphEvent",
    "BasePlugin",
    "GraphHistoryEntry",
    "GraphNode",
    "GraphEnd",
    "PydanticGraphContext",
]

# Type variables
GraphState = TypeVar("GraphState")
T = TypeVar("T")

# Re-export from pydantic-graph for convenience
GraphNode = BaseNode
GraphEnd = End
PydanticGraphContext = GraphRunContext


@dataclass
class ActionSettings:
    """Settings for an action in a graph."""

    model: Optional[LanguageModelName | str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: List[Callable] = field(default_factory=list)
    start: bool = False
    terminates: bool = False
    xml: Optional[str] = None
    next: Optional[Union[str, List[str]]] = None
    read_history: bool = False
    persist_history: bool = False
    condition: Optional[str] = None
    name: Optional[str] = None
    instructions: Optional[str] = None
    verbose: bool = False
    debug: bool = False
    # Agent end strategy parameters
    max_steps: Optional[int] = None
    end_strategy: Optional[Literal["tool"]] = None
    end_tool: Optional[Callable] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphHistoryEntry:
    """Entry in the graph execution history."""

    index: int
    """The index of the history entry."""

    field: str
    """The name of the field/action that triggered this history entry."""

    steps: List[LanguageModelResponse] = field(default_factory=list)
    """The steps that were executed to produce this history entry."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about this history entry."""


@dataclass
class ActionInfo:
    """Information about an action in a graph."""

    name: str
    """The name of the action."""

    func: Callable
    """The function that implements the action."""

    settings: "ActionSettings"
    """Settings for the action."""

    is_start: bool = False
    """Whether this is the start action."""

    parameters: Dict[str, Any] = field(default_factory=dict)
    """Parameter information for the action."""


@dataclass
class GraphEvent:
    """Event emitted during graph execution that can be modified by plugins."""

    field: str
    """The name of the field that triggered the event."""

    output: Any
    """The output value of the field that triggered the event."""

    type: str
    """The type of this event (e.g., 'tool_call', 'final_response', 'action_start')."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the event."""

    _hooks: List[Callable] = field(default_factory=list)
    """Internal list of hooks registered for this event."""

    def on(self, func: Callable) -> Callable:
        """Hook to look into and augment this event."""
        self._hooks.append(func)
        return func

    def trigger_hooks(self) -> "GraphEvent":
        """Trigger all registered hooks for this event."""
        result = self
        for hook in self._hooks:
            hook_result = hook(result)
            if hook_result is not None:
                result = hook_result
        return result


# Enhanced GraphContext that wraps pydantic-graph's GraphRunContext
@dataclass
class GraphContext(Generic[GraphState]):
    """Context object for graph execution, providing access to state and plugin system."""

    pydantic_context: GraphRunContext[GraphState]
    """The underlying pydantic-graph context."""

    plugins: List["BasePlugin"] = field(default_factory=list)
    """Active plugins for this graph execution."""

    history: List[GraphHistoryEntry] = field(default_factory=list)
    """The history of the graph's execution."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the graph's execution."""

    @property
    def state(self) -> GraphState:
        """Get the current state."""
        return self.pydantic_context.state

    @property
    def deps(self) -> Any:
        """Get the dependencies."""
        return self.pydantic_context.deps

    def get_field(self, field_name: str) -> Any:
        """Get a field value from the state."""
        if hasattr(self.state, field_name):
            return getattr(self.state, field_name)
        elif hasattr(self.state, "__getitem__"):
            return self.state[field_name]
        else:
            raise AttributeError(f"Field '{field_name}' not found in state")

    def set_field(self, field_name: str, value: Any) -> None:
        """Set a field value in the state."""
        if hasattr(self.state, field_name):
            setattr(self.state, field_name, value)
        elif hasattr(self.state, "__setitem__"):
            self.state[field_name] = value
        else:
            raise AttributeError(f"Cannot set field '{field_name}' in state")

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to fields"""
        return self.get_field(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like assignment to fields"""
        self.set_field(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get field value with optional default"""
        try:
            return self.get_field(key)
        except AttributeError:
            return default

    def emit_event(self, event: GraphEvent) -> GraphEvent:
        """Emit an event and allow plugins to modify it."""
        # Apply plugin modifications
        for plugin in self.plugins:
            if hasattr(plugin, "on_event"):
                event = plugin.on_event(event)

        # Trigger any hooks registered on the event
        event = event.trigger_hooks()

        return event


class BasePlugin:
    """Base class for graph plugins that can modify execution."""

    def __init__(self, **kwargs: Any):
        """Initialize the plugin with configuration options."""
        self.config = kwargs

    def on_event(self, event: GraphEvent) -> GraphEvent:
        """Handle and potentially modify an event."""
        return event

    def on_graph_start(self, context: GraphContext[Any]) -> None:
        """Called when graph execution starts."""
        pass

    def on_graph_end(self, context: GraphContext[Any]) -> None:
        """Called when graph execution ends."""
        pass

    def on_action_start(self, context: GraphContext[Any], action_name: str) -> None:
        """Called when an action starts executing."""
        pass

    def on_action_end(
        self, context: GraphContext[Any], action_name: str, result: Any
    ) -> None:
        """Called when an action finishes executing."""
        pass


class GraphResponse(AgentResponse[T, GraphState], Generic[T, GraphState]):
    """A response generated by the execution of a graph."""

    type: str = "graph"
    """The type of this response. Always 'graph'."""

    output: T
    """The final output of the graph's execution."""

    state: GraphState | None = None
    """The final state object after graph execution."""

    history: List[GraphHistoryEntry] = Field(default_factory=list)
    """The total history of the graph's execution."""

    start_node: Optional[str] = None
    """The name of the start node that was executed."""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Metadata about the graph's execution."""

    nodes_executed: List[str] = Field(default_factory=list)
    """List of node names that were executed."""

    steps: List[LanguageModelResponse] = Field(default_factory=list)
    """The steps that were executed to produce this response."""

    @property
    def fields(self) -> Dict[str, Any]:
        """Access to the graph field values"""
        if self.state is None:
            return {}
        if hasattr(self.state, "model_dump"):
            return self.state.model_dump()
        elif hasattr(self.state, "__dict__"):
            return self.state.__dict__
        elif hasattr(self.state, "items"):
            return dict(self.state.items())
        return {}

    def __getattr__(self, name: str) -> Any:
        """Allow accessing fields via dot notation"""
        if name in self.fields:
            return self.fields[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    @cached
    def __str__(self) -> str:
        """Pretty prints the response object."""
        output = ">>> GraphResponse:"

        if self.output or self.content:
            output += f"\n{self.output if self.output else self.content}"
        else:
            output += f"\n{self.completion}"

        output += f"\n\n>>> Model: {self.model}"
        output += f"\n>>> Start Node: {self.start_node or 'Unknown'}"
        output += f"\n>>> Nodes Executed: {len(self.nodes_executed)}"

        if self.nodes_executed:
            output += f" ({', '.join(self.nodes_executed)})"

        output += f"\n>>> Output Type: {get_type_description(type(self.output))}"

        # Calculate total tool calls across all steps
        total_tool_calls = 0
        for step in self.steps:
            if hasattr(step, "has_tool_calls") and step.has_tool_calls():
                total_tool_calls += len(step.tool_calls)

        output += f"\n>>> Total Tool Calls: {total_tool_calls}"

        # Show state values if available
        if self.state:
            output += f"\n>>> State: {self._format_state_display()}"

        return output

    def _format_state_display(self) -> str:
        """Format state values for display in string representation."""
        try:
            items = []
            for key, value in self.fields.items():
                if isinstance(value, str):
                    # Truncate long strings
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    items.append(f"{key}='{display_value}'")
                else:
                    items.append(f"{key}={value}")

            return "{" + ", ".join(items) + "}"
        except Exception:
            return str(self.state)


class GraphResponseChunk(BaseModel, Generic[T]):
    """A chunk from a graph response stream representing a single execution step."""

    step_number: int
    """The step number of this chunk."""

    node_name: str
    """The name of the node that was executed."""

    output: T | None = None
    """The output value from this step."""

    content: str | None = None
    """The content string from this step."""

    model: str | None = None
    """The model name used for this step."""

    is_final: bool = False
    """Whether this is the final chunk."""

    state: Any = None
    """The state after this step."""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Additional metadata about this step."""

    def __bool__(self) -> bool:
        """Check if this chunk has meaningful content."""
        return bool(self.output or self.content)

    def __str__(self) -> str:
        """String representation of the chunk."""
        output = f"GraphResponseChunk(step={self.step_number}, node={self.node_name}, final={self.is_final})"

        # Show content if available
        if self.output or self.content:
            content_preview = str(self.output if self.output else self.content)
            if len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
            output += f"\nContent: {content_preview}"

        return output


class GraphStream(BaseGenAIModelStream[GraphResponseChunk[T]], Generic[T, GraphState]):
    """Stream of graph execution steps that can be used in sync and async contexts."""

    def __init__(
        self,
        graph: "BaseGraph[GraphState, T]",
        start_node: Any,
        state: Optional[GraphState] = None,
        **kwargs: Any,
    ):
        """Initialize the graph stream.

        Args:
            graph: The BaseGraph instance
            start_node: The starting node for execution
            state: Optional state object
            **kwargs: Additional parameters
        """
        super().__init__(
            type="graph",
            model=graph._global_model or "openai/gpt-4o-mini",
            stream=None,
        )
        self.graph = graph
        self.start_node = start_node
        self.state = state
        self.kwargs = kwargs
        self.current_step = 0
        self.is_done = False
        self._pydantic_iterator = None
        self._async_pydantic_iterator = None

    def __iter__(self) -> Iterator[GraphResponseChunk[T]]:
        """Iterate over graph execution steps."""
        if not self.graph._pydantic_graph:
            raise ValueError("Graph not initialized")

        # Create the pydantic-graph iterator
        pydantic_iter = self.graph._pydantic_graph.iter(
            self.start_node, state=self.state
        )
        self._pydantic_iterator = pydantic_iter

        try:
            for node_result in pydantic_iter:
                self.current_step += 1

                # Extract information from the pydantic-graph result
                node_name = getattr(node_result, "__class__", {}).get(
                    "__name__", "unknown"
                )
                if hasattr(node_result, "action_name"):
                    node_name = node_result.action_name

                # Extract output from the result
                output = None
                content = None
                if hasattr(node_result, "data"):
                    output = node_result.data
                    content = str(node_result.data)
                elif hasattr(node_result, "output"):
                    output = node_result.output
                    content = str(node_result.output)
                else:
                    output = str(node_result)
                    content = str(node_result)

                # Determine if this is the final step
                is_final = isinstance(node_result, End)

                # Create and yield chunk
                chunk = GraphResponseChunk(
                    step_number=self.current_step,
                    node_name=node_name,
                    output=output,
                    content=content,
                    model=self.model,
                    is_final=is_final,
                    state=self.state,
                    metadata=self.kwargs,
                )

                yield chunk

                if is_final:
                    self.is_done = True
                    break

        except Exception as e:
            # Handle any errors during iteration
            error_chunk = GraphResponseChunk(
                step_number=self.current_step + 1,
                node_name="error",
                output=None,
                content=f"Error during graph execution: {str(e)}",
                model=self.model,
                is_final=True,
                state=self.state,
                metadata={"error": str(e)},
            )
            yield error_chunk
            self.is_done = True

    def __aiter__(self) -> AsyncIterator[GraphResponseChunk[T]]:
        """Async iterator for graph execution."""
        return self

    async def __anext__(self) -> GraphResponseChunk[T]:
        """Get the next chunk in async iteration."""
        if not self.graph._pydantic_graph:
            raise ValueError("Graph not initialized")

        if self.is_done:
            raise StopAsyncIteration

        # Initialize async iterator if not already done
        if self._async_pydantic_iterator is None:
            self._async_pydantic_iterator = self.graph._pydantic_graph.iter(
                self.start_node, state=self.state
            ).__aiter__()

        try:
            node_result = await self._async_pydantic_iterator.__anext__()
            self.current_step += 1

            # Extract information from the pydantic-graph result
            node_name = getattr(node_result, "__class__", {}).get("__name__", "unknown")
            if hasattr(node_result, "action_name"):
                node_name = node_result.action_name

            # Extract output from the result
            output = None
            content = None
            if hasattr(node_result, "data"):
                output = node_result.data
                content = str(node_result.data)
            elif hasattr(node_result, "output"):
                output = node_result.output
                content = str(node_result.output)
            else:
                output = str(node_result)
                content = str(node_result)

            # Determine if this is the final step
            is_final = isinstance(node_result, End)

            # Create chunk
            chunk = GraphResponseChunk(
                step_number=self.current_step,
                node_name=node_name,
                output=output,
                content=content,
                model=self.model,
                is_final=is_final,
                state=self.state,
                metadata=self.kwargs,
            )

            if is_final:
                self.is_done = True

            return chunk

        except StopAsyncIteration:
            self.is_done = True
            raise
        except Exception as e:
            # Handle any errors during iteration
            error_chunk = GraphResponseChunk(
                step_number=self.current_step + 1,
                node_name="error",
                output=None,
                content=f"Error during graph execution: {str(e)}",
                model=self.model,
                is_final=True,
                state=self.state,
                metadata={"error": str(e)},
            )
            self.is_done = True
            return error_chunk

    def collect(self) -> GraphResponse[T, GraphState]:
        """Collect all steps and return final graph response."""
        chunks = []
        final_chunk = None

        for chunk in self:
            chunks.append(chunk)
            if chunk.is_final:
                final_chunk = chunk
                break

        if final_chunk is None:
            raise RuntimeError("No final chunk generated by graph execution")

        # Create response from final chunk
        return GraphResponse(
            type="graph",
            model=self.model,
            output=final_chunk.output,
            content=final_chunk.content,
            completion=None,
            state=final_chunk.state,
            history=[],
            start_node=getattr(self.start_node, "action_name", "unknown"),
            nodes_executed=[chunk.node_name for chunk in chunks],
            metadata=final_chunk.metadata,
        )

    async def async_collect(self) -> GraphResponse[T, GraphState]:
        """Collect all steps and return final graph response."""
        chunks = []
        final_chunk = None

        async for chunk in self:
            chunks.append(chunk)
            if chunk.is_final:
                final_chunk = chunk
                break

        if final_chunk is None:
            raise RuntimeError("No final chunk generated by graph execution")

        # Create response from final chunk
        return GraphResponse(
            type="graph",
            model=self.model,
            output=final_chunk.output,
            content=final_chunk.content,
            completion=None,
            state=final_chunk.state,
            history=[],
            start_node=getattr(self.start_node, "action_name", "unknown"),
            nodes_executed=[chunk.node_name for chunk in chunks],
            metadata=final_chunk.metadata,
        )
