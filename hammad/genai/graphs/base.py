"""hammad.genai.graphs.base - Graph implementation using pydantic-graph with Agent/LanguageModel integration"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Generic,
    Union,
    Callable,
    get_type_hints,
    ParamSpec,
    Awaitable,
)
from typing_extensions import Literal
from dataclasses import dataclass, field
import inspect
from functools import wraps
import asyncio

from pydantic_graph import BaseNode, End, Graph as PydanticGraph, GraphRunContext
from pydantic import BaseModel
from ..models.language.utils import (
    LanguageModelRequestBuilder,
    parse_messages_input,
    consolidate_system_messages,
)

from ..agents.agent import Agent
from ..agents.types.agent_response import AgentResponse
from ..agents.types.agent_messages import AgentMessages
from ..models.language.model import LanguageModel
from ..models.language.types.language_model_name import LanguageModelName
from .types import (
    GraphContext,
    GraphResponse,
    GraphStream,
    GraphResponseChunk,
    GraphState,
    BasePlugin,
    ActionSettings,
    GraphHistoryEntry,
)

__all__ = [
    "BaseGraph",
    "action",
    "ActionNode",
    "GraphBuilder",
    "GraphStream",
    "GraphResponseChunk",
]

T = TypeVar("T")
StateT = TypeVar("StateT")
P = ParamSpec("P")


class ActionNode(BaseNode[StateT, None, Any]):
    """A pydantic-graph node that wraps a user-defined action function."""

    def __init__(
        self,
        action_name: str,
        action_func: Callable,
        settings: ActionSettings,
        **action_params: Any,
    ):
        """Initialize the action node with parameters."""
        self.action_name = action_name
        self.action_func = action_func
        self.settings = settings

        # Store action parameters as instance attributes for pydantic-graph
        for param_name, param_value in action_params.items():
            setattr(self, param_name, param_value)

    async def run(self, ctx: GraphRunContext[StateT]) -> Union[BaseNode, End]:
        """Execute the action function using Agent/LanguageModel infrastructure."""

        # Create enhanced context that wraps pydantic-graph context
        enhanced_ctx = GraphContext(
            pydantic_context=ctx,
            plugins=[],  # Will be populated by BaseGraph
            history=[],
            metadata={},
        )

        # Extract action parameters from self
        action_params = {}
        sig = inspect.signature(self.action_func)
        for param_name in sig.parameters:
            if param_name not in ("self", "ctx", "context", "agent", "language_model"):
                if hasattr(self, param_name):
                    action_params[param_name] = getattr(self, param_name)

        # Get the docstring from the action function to use as field-level instructions
        field_instructions = self.action_func.__doc__ or ""

        # Get the global system prompt from the graph class docstring
        global_system_prompt = ""
        if hasattr(self, "_graph_docstring"):
            global_system_prompt = self._graph_docstring

        # Add well-defined step execution context
        step_context = f"""
You are executing step '{self.action_name}' in a multi-step graph workflow.

Step Purpose: {field_instructions or "Execute the requested action"}

Execution Guidelines:
- Focus on completing this specific step's objective
- Provide clear, actionable output that can be used by subsequent steps
- If this step involves decision-making, be explicit about your reasoning
- Maintain consistency with the overall workflow context
"""

        # Check if the action function expects to handle the language model itself
        expects_language_model = (
            "language_model" in sig.parameters or "agent" in sig.parameters
        )

        if expects_language_model:
            # Legacy mode: action function expects to handle language model
            # Combine global system prompt with field-level instructions and step context
            combined_instructions = global_system_prompt
            if step_context:
                combined_instructions += f"\n\n{step_context}"
            if field_instructions and field_instructions not in combined_instructions:
                combined_instructions += (
                    f"\n\nAdditional Instructions: {field_instructions}"
                )

            # Get verbose/debug flags and language model kwargs from the node
            verbose = getattr(self, "_verbose", self.settings.verbose)
            debug = getattr(self, "_debug", self.settings.debug)
            language_model_kwargs = getattr(self, "_language_model_kwargs", {})

            # Get end strategy parameters from node or settings
            max_steps = getattr(self, "_max_steps", self.settings.max_steps)
            end_strategy = getattr(self, "_end_strategy", self.settings.end_strategy)
            end_tool = getattr(self, "_end_tool", self.settings.end_tool)

            if self.settings.tools or self.settings.instructions:
                agent = Agent(
                    name=self.settings.name or self.action_name,
                    instructions=self.settings.instructions or combined_instructions,
                    model=self.settings.model or "openai/gpt-4o-mini",
                    tools=self.settings.tools,
                    max_steps=max_steps,
                    end_strategy=end_strategy,
                    end_tool=end_tool,
                    verbose=verbose,
                    debug=debug,
                    **language_model_kwargs,
                )
                # Pass history to context if available
                history = getattr(self, "_history", None)
                if history:
                    enhanced_ctx.metadata["history"] = history

                if asyncio.iscoroutinefunction(self.action_func):
                    result = await self.action_func(
                        enhanced_ctx, agent, **action_params
                    )
                else:
                    result = self.action_func(enhanced_ctx, agent, **action_params)
            else:
                language_model = LanguageModel(
                    model=self.settings.model or "openai/gpt-4o-mini",
                    verbose=verbose,
                    debug=debug,
                    **language_model_kwargs,
                )
                # Pass history to context if available
                history = getattr(self, "_history", None)
                if history:
                    enhanced_ctx.metadata["history"] = history

                if asyncio.iscoroutinefunction(self.action_func):
                    result = await self.action_func(
                        enhanced_ctx, language_model, **action_params
                    )
                else:
                    result = self.action_func(
                        enhanced_ctx, language_model, **action_params
                    )
        else:
            # New mode: framework handles language model internally
            # Build the user message from the action parameters with clear context
            user_message = ""
            if action_params:
                if len(action_params) == 1:
                    # Single parameter - use its value directly with context
                    param_value = list(action_params.values())[0]
                    user_message = f"Process the following input for step '{self.action_name}':\n\n{param_value}"
                else:
                    # Multiple parameters - format them clearly
                    param_list = "\n".join(
                        f"- {k}: {v}" for k, v in action_params.items()
                    )
                    user_message = f"Execute step '{self.action_name}' with the following parameters:\n\n{param_list}"
            else:
                # No parameters - provide clear step instruction
                user_message = f"Execute the '{self.action_name}' step of the workflow."

            # Combine global system prompt with step context and field-level instructions
            combined_instructions = global_system_prompt
            if step_context:
                combined_instructions += f"\n\n{step_context}"
            if field_instructions and field_instructions not in combined_instructions:
                combined_instructions += (
                    f"\n\nAdditional Instructions: {field_instructions}"
                )

            # Add execution guidelines for framework mode
            execution_guidelines = """
            
Execution Guidelines:
- Provide a clear, direct response that addresses the step's objective
- Your output will be used as input for subsequent workflow steps
- Be concise but comprehensive in your response
- If making decisions or analysis, show your reasoning process
"""
            combined_instructions += execution_guidelines

            # Get verbose/debug flags and language model kwargs from the node
            verbose = getattr(self, "_verbose", self.settings.verbose)
            debug = getattr(self, "_debug", self.settings.debug)
            language_model_kwargs = getattr(self, "_language_model_kwargs", {})

            # Get end strategy parameters from node or settings
            max_steps = getattr(self, "_max_steps", self.settings.max_steps)
            end_strategy = getattr(self, "_end_strategy", self.settings.end_strategy)
            end_tool = getattr(self, "_end_tool", self.settings.end_tool)

            # Determine if we need to use Agent or LanguageModel
            if self.settings.tools or self.settings.instructions:
                # Use Agent for complex operations with tools/instructions
                agent = Agent(
                    name=self.settings.name or self.action_name,
                    instructions=self.settings.instructions or combined_instructions,
                    model=self.settings.model or "openai/gpt-4o-mini",
                    tools=self.settings.tools,
                    max_steps=max_steps,
                    end_strategy=end_strategy,
                    end_tool=end_tool,
                    verbose=verbose,
                    debug=debug,
                    **language_model_kwargs,
                )

                # Get history if available
                history = getattr(self, "_history", None)

                # Run the agent with the user message and history
                if history:
                    # If history is provided, we need to combine it with the user message
                    # The history should be the conversation context, and user_message is the new input
                    combined_messages = parse_messages_input(history)
                    combined_messages.append({"role": "user", "content": user_message})
                    agent_result = await agent.async_run(combined_messages)
                else:
                    agent_result = await agent.async_run(user_message)
                result = agent_result.output
            else:
                # Use LanguageModel for simple operations
                language_model = LanguageModel(
                    model=self.settings.model or "openai/gpt-4o-mini",
                    verbose=verbose,
                    debug=debug,
                    **language_model_kwargs,
                )

                # Get history if available
                history = getattr(self, "_history", None)

                # Create messages using the language model utils
                if history:
                    # If history is provided, use it as the base messages
                    messages = parse_messages_input(
                        history, instructions=combined_instructions
                    )
                    # Then add the user message from action parameters
                    messages.append({"role": "user", "content": user_message})
                else:
                    # Otherwise, use the user message
                    messages = parse_messages_input(
                        user_message, instructions=combined_instructions
                    )
                messages = consolidate_system_messages(messages)

                # Run the language model with the consolidated messages
                lm_result = await language_model.async_run(messages)
                result = lm_result.output

            # Get the return type annotation to determine expected output type
            return_type = sig.return_annotation
            if return_type != inspect.Parameter.empty and return_type != str:
                # If the action expects a specific return type, try to parse it
                # For now, we'll just return the string result
                # In a full implementation, we'd use structured output parsing
                pass

        # Handle the result based on settings
        if isinstance(result, (BaseNode, End)):
            return result
        elif self.settings.terminates:
            return End(result)
        else:
            # For non-terminating actions that don't return a node, continue to next
            # This would be more sophisticated in a real implementation with routing
            return End(result)


class ActionDecorator:
    """Decorator for creating actions that become nodes in the graph."""

    def __init__(self):
        self._actions: Dict[str, Type[ActionNode]] = {}
        self._start_action: Optional[str] = None

    def __call__(
        self,
        func: Optional[Callable] = None,
        *,
        model: Optional[LanguageModelName | str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Callable]] = None,
        start: bool = False,
        terminates: bool = False,
        xml: Optional[str] = None,
        next: Optional[Union[str, List[str]]] = None,
        read_history: bool = False,
        persist_history: bool = False,
        condition: Optional[str] = None,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
        debug: bool = False,
        # Agent end strategy parameters
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        **kwargs: Any,
    ) -> Union[Callable, Type[ActionNode]]:
        """Main action decorator."""

        settings = ActionSettings(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools or [],
            start=start,
            terminates=terminates,
            xml=xml,
            next=next,
            read_history=read_history,
            persist_history=persist_history,
            condition=condition,
            name=name,
            instructions=instructions,
            verbose=verbose,
            debug=debug,
            max_steps=max_steps,
            end_strategy=end_strategy,
            end_tool=end_tool,
            kwargs=kwargs,
        )

        def decorator(f: Callable) -> Callable:
            action_name = name or f.__name__

            # Create a dynamic ActionNode class for this specific action
            class DynamicActionNode(ActionNode[StateT]):
                def __init__(self, **action_params):
                    super().__init__(
                        action_name=action_name,
                        action_func=f,
                        settings=settings,
                        **action_params,
                    )

            # Store the action
            self._actions[action_name] = DynamicActionNode
            if start:
                if self._start_action is not None:
                    raise ValueError(
                        f"Multiple start actions: {self._start_action} and {action_name}"
                    )
                self._start_action = action_name

            # Return the original function with metadata attached
            f._action_name = action_name
            f._action_settings = settings
            f._action_node_class = DynamicActionNode
            f._is_start = start

            return f

        if func is None:
            return decorator
        else:
            return decorator(func)

    def start(
        self, func: Optional[Callable] = None, **kwargs
    ) -> Union[Callable, Type[ActionNode]]:
        """Decorator for start actions."""
        return self.__call__(func, start=True, **kwargs)

    def end(
        self, func: Optional[Callable] = None, **kwargs
    ) -> Union[Callable, Type[ActionNode]]:
        """Decorator for end actions."""
        return self.__call__(func, terminates=True, **kwargs)


# Global action decorator
action = ActionDecorator()


class GraphBuilder(Generic[StateT, T]):
    """Builder for creating graphs with plugins and configuration."""

    def __init__(self, graph_class: Type["BaseGraph[StateT, T]"]):
        self.graph_class = graph_class
        self.plugins: List[BasePlugin] = []
        self.global_model: Optional[LanguageModelName] = None
        self.global_settings: Dict[str, Any] = {}

    def with_plugin(self, plugin: BasePlugin) -> "GraphBuilder[StateT, T]":
        """Add a plugin to the graph."""
        self.plugins.append(plugin)
        return self

    def with_model(self, model: LanguageModelName) -> "GraphBuilder[StateT, T]":
        """Set the global model for the graph."""
        self.global_model = model
        return self

    def with_settings(self, **settings: Any) -> "GraphBuilder[StateT, T]":
        """Set global settings for the graph."""
        self.global_settings.update(settings)
        return self

    def build(self) -> "BaseGraph[StateT, T]":
        """Build the graph instance."""
        instance = self.graph_class()
        instance._plugins = self.plugins
        instance._global_model = self.global_model
        instance._global_settings = self.global_settings
        instance._initialize()
        return instance


class BaseGraph(Generic[StateT, T]):
    """Base class for graphs that provides action decorator support on top of pydantic-graph."""

    def __init__(self, state: Optional[StateT] = None):
        self._plugins: List[BasePlugin] = []
        self._global_model: Optional[LanguageModelName] = None
        self._global_settings: Dict[str, Any] = {}
        self._pydantic_graph: Optional[PydanticGraph] = None
        self._action_nodes: Dict[str, Type[ActionNode]] = {}
        self._start_action_name: Optional[str] = None
        self._start_action_func: Optional[Callable] = None
        self._state: Optional[StateT] = state
        self._state_class: Optional[Type[StateT]] = None
        # Initialize the graph automatically
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the graph by collecting actions and creating the pydantic graph."""
        self._collect_state_class()
        self._collect_actions()
        self._create_pydantic_graph()

    def _collect_state_class(self) -> None:
        """Collect the State class if defined in the graph."""
        # Look for a State class defined in the graph
        for attr_name in dir(self.__class__):
            attr = getattr(self.__class__, attr_name)
            if (
                isinstance(attr, type)
                and attr_name == "State"
                and attr != self.__class__
            ):
                self._state_class = attr
                # If no state was provided in constructor, try to create default instance
                if self._state is None:
                    try:
                        if hasattr(attr, "__call__"):
                            self._state = attr()
                    except Exception:
                        # If we can't create a default instance, leave it as None
                        pass
                break

    def _collect_actions(self) -> None:
        """Collect all actions defined in the graph class."""
        actions_found = []

        # Get the graph class docstring for global system prompt
        graph_docstring = self.__class__.__doc__ or ""

        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_action_name"):
                action_name = attr._action_name
                action_node_class = attr._action_node_class

                self._action_nodes[action_name] = action_node_class
                actions_found.append((action_name, attr))

                if hasattr(attr, "_is_start") and attr._is_start:
                    if self._start_action_name is not None:
                        raise ValueError(
                            f"Multiple start actions: {self._start_action_name} and {action_name}"
                        )
                    self._start_action_name = action_name
                    self._start_action_func = attr

        # If no explicit start action was defined and we have exactly one action,
        # automatically make it the start action
        if self._start_action_name is None and len(actions_found) == 1:
            action_name, action_func = actions_found[0]
            self._start_action_name = action_name
            self._start_action_func = action_func

        # Store the graph docstring in all action nodes for access during execution
        for action_node_class in self._action_nodes.values():
            # We'll add this to the action node instances when they're created
            action_node_class._graph_docstring = graph_docstring

    def _create_pydantic_graph(self) -> None:
        """Create the underlying pydantic graph from collected actions."""
        if not self._action_nodes:
            raise ValueError("No actions defined in graph")

        # Create the pydantic graph with the node classes
        node_classes = list(self._action_nodes.values())
        self._pydantic_graph = PydanticGraph(nodes=node_classes)

    def _get_start_action_signature(self) -> inspect.Signature:
        """Get the signature of the start action for type-safe run methods."""
        if self._start_action_func is None:
            return inspect.Signature([])

        sig = inspect.signature(self._start_action_func)
        # Filter out 'self', 'ctx'/'context', 'agent', 'language_model' parameters
        params = []
        for param_name, param in sig.parameters.items():
            if param_name not in ("self", "ctx", "context", "agent", "language_model"):
                params.append(param)

        return inspect.Signature(params)

    def run(
        self,
        *args,
        state: Optional[StateT] = None,
        history: Optional[AgentMessages] = None,
        verbose: bool = False,
        debug: bool = False,
        **kwargs,
    ) -> GraphResponse[T, StateT]:
        """
        Run the graph with the given parameters.
        The signature is dynamically determined by the start action.

        Args:
            *args: Arguments for the start action
            state: Optional state object to use for the execution
            history: Optional chat history in various formats (str, messages list, History object)
            verbose: Enable verbose logging
            debug: Enable debug logging
            **kwargs: Additional keyword arguments for the start action and language model

        Returns:
            GraphResponse containing the execution result and metadata
        """

        if self._start_action_name is None:
            raise ValueError("No start action defined")

        # Get the start action node class
        start_node_class = self._action_nodes[self._start_action_name]

        # Create the start node instance with the provided arguments
        start_sig = self._get_start_action_signature()

        # Separate language model kwargs from start action kwargs
        language_model_kwargs = {}
        start_action_kwargs = {}

        # Language model specific parameters
        lm_params = {
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "stream",
            "response_format",
            "seed",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "functions",
            "function_call",
            "user",
            "system",
            "n",
            "echo",
            "logprobs",
            "top_logprobs",
            "suffix",
            "max_retries",
            "timeout",
            "model",
            "type",
            "instructor_mode",
            "max_steps",
            "end_strategy",
            "end_tool",
        }

        for key, value in kwargs.items():
            if key in lm_params:
                language_model_kwargs[key] = value
            else:
                start_action_kwargs[key] = value

        # Bind arguments to start action parameters
        try:
            bound_args = start_sig.bind(*args, **start_action_kwargs)
            bound_args.apply_defaults()
        except TypeError as e:
            raise ValueError(
                f"Invalid arguments for start action '{self._start_action_name}': {e}"
            )

        start_node = start_node_class(**bound_args.arguments)
        # Pass the graph docstring to the node for global system prompt
        start_node._graph_docstring = self.__class__.__doc__ or ""
        # Pass verbose/debug flags and language model kwargs
        start_node._verbose = verbose
        start_node._debug = debug
        start_node._language_model_kwargs = language_model_kwargs
        # Pass history if provided
        start_node._history = history

        # Pass end strategy parameters if provided
        if "max_steps" in language_model_kwargs:
            start_node._max_steps = language_model_kwargs["max_steps"]
        if "end_strategy" in language_model_kwargs:
            start_node._end_strategy = language_model_kwargs["end_strategy"]
        if "end_tool" in language_model_kwargs:
            start_node._end_tool = language_model_kwargs["end_tool"]

        # Run the pydantic graph
        if not self._pydantic_graph:
            raise ValueError("Graph not initialized")

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state

        # Execute the graph using pydantic-graph
        try:
            # For now, use sync execution - would implement proper async support
            result = self._pydantic_graph.run_sync(start_node, state=execution_state)

            # Extract the actual output from pydantic-graph result
            if hasattr(result, "data"):
                output = result.data
            elif hasattr(result, "output"):
                output = result.output
            else:
                output = str(result)

            # Create our response object
            return GraphResponse(
                type="graph",
                model=self._global_model or "openai/gpt-4o-mini",
                output=output,
                content=str(output),
                completion=None,
                state=execution_state,
                history=[],  # Would be populated from pydantic-graph execution
                start_node=self._start_action_name,
                nodes_executed=[self._start_action_name],  # Would track from execution
                metadata={},
            )

        except Exception as e:
            raise RuntimeError(f"Graph execution failed: {e}") from e

    def iter(
        self,
        *args,
        state: Optional[StateT] = None,
        history: Optional[AgentMessages] = None,
        verbose: bool = False,
        debug: bool = False,
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        **kwargs,
    ) -> GraphStream[T, StateT]:
        """
        Create an iterator for the graph execution.
        The signature is dynamically determined by the start action.

        Args:
            *args: Arguments for the start action
            state: Optional state object to use for the execution
            history: Optional chat history in various formats (str, messages list, History object)
            verbose: Enable verbose logging
            debug: Enable debug logging
            max_steps: Maximum number of steps to execute
            end_strategy: Strategy for ending execution
            end_tool: Tool to use for ending execution
            **kwargs: Additional keyword arguments for the start action and language model

        Returns:
            GraphStream that can be iterated over to get each execution step
        """

        if self._start_action_name is None:
            raise ValueError("No start action defined")

        # Get the start action node class
        start_node_class = self._action_nodes[self._start_action_name]

        # Create the start node instance with the provided arguments
        start_sig = self._get_start_action_signature()

        # Separate language model kwargs from start action kwargs
        language_model_kwargs = {}
        start_action_kwargs = {}

        # Language model specific parameters
        lm_params = {
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "stream",
            "response_format",
            "seed",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "functions",
            "function_call",
            "user",
            "system",
            "n",
            "echo",
            "logprobs",
            "top_logprobs",
            "suffix",
            "max_retries",
            "timeout",
            "model",
            "type",
            "instructor_mode",
            "max_steps",
            "end_strategy",
            "end_tool",
        }

        for key, value in kwargs.items():
            if key in lm_params:
                language_model_kwargs[key] = value
            else:
                start_action_kwargs[key] = value

        try:
            bound_args = start_sig.bind(*args, **start_action_kwargs)
            bound_args.apply_defaults()
        except TypeError as e:
            raise ValueError(
                f"Invalid arguments for start action '{self._start_action_name}': {e}"
            )

        start_node = start_node_class(**bound_args.arguments)
        # Pass the graph docstring to the node for global system prompt
        start_node._graph_docstring = self.__class__.__doc__ or ""
        # Pass verbose/debug flags and language model kwargs
        start_node._verbose = verbose
        start_node._debug = debug
        start_node._language_model_kwargs = language_model_kwargs
        # Pass history if provided
        start_node._history = history

        # Pass end strategy parameters if provided
        if max_steps is not None:
            start_node._max_steps = max_steps
        if end_strategy is not None:
            start_node._end_strategy = end_strategy
        if end_tool is not None:
            start_node._end_tool = end_tool

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state

        # Create and return GraphStream
        return GraphStream(
            graph=self,
            start_node=start_node,
            state=execution_state,
            verbose=verbose,
            debug=debug,
            max_steps=max_steps,
            end_strategy=end_strategy,
            end_tool=end_tool,
            **language_model_kwargs,
        )

    async def async_run(
        self,
        *args,
        state: Optional[StateT] = None,
        history: Optional[AgentMessages] = None,
        verbose: bool = False,
        debug: bool = False,
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        **kwargs,
    ) -> GraphResponse[T, StateT]:
        """Async version of run.

        Args:
            *args: Arguments for the start action
            state: Optional state object to use for the execution
            history: Optional chat history in various formats (str, messages list, History object)
            verbose: Enable verbose logging
            debug: Enable debug logging
            **kwargs: Additional keyword arguments for the start action and language model

        Returns:
            GraphResponse containing the execution result and metadata
        """

        if self._start_action_name is None:
            raise ValueError("No start action defined")

        # Get the start action node class
        start_node_class = self._action_nodes[self._start_action_name]

        # Create the start node instance with the provided arguments
        start_sig = self._get_start_action_signature()

        # Separate language model kwargs from start action kwargs
        language_model_kwargs = {}
        start_action_kwargs = {}

        # Language model specific parameters
        lm_params = {
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "stream",
            "response_format",
            "seed",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "functions",
            "function_call",
            "user",
            "system",
            "n",
            "echo",
            "logprobs",
            "top_logprobs",
            "suffix",
            "max_retries",
            "timeout",
            "model",
            "type",
            "instructor_mode",
            "max_steps",
            "end_strategy",
            "end_tool",
        }

        for key, value in kwargs.items():
            if key in lm_params:
                language_model_kwargs[key] = value
            else:
                start_action_kwargs[key] = value

        try:
            bound_args = start_sig.bind(*args, **start_action_kwargs)
            bound_args.apply_defaults()
        except TypeError as e:
            raise ValueError(
                f"Invalid arguments for start action '{self._start_action_name}': {e}"
            )

        start_node = start_node_class(**bound_args.arguments)
        # Pass the graph docstring to the node for global system prompt
        start_node._graph_docstring = self.__class__.__doc__ or ""
        # Pass verbose/debug flags and language model kwargs
        start_node._verbose = verbose
        start_node._debug = debug
        start_node._language_model_kwargs = language_model_kwargs
        # Pass history if provided
        start_node._history = history

        # Pass end strategy parameters if provided
        if max_steps is not None:
            start_node._max_steps = max_steps
        if end_strategy is not None:
            start_node._end_strategy = end_strategy
        if end_tool is not None:
            start_node._end_tool = end_tool

        # Run the pydantic graph asynchronously
        if not self._pydantic_graph:
            raise ValueError("Graph not initialized")

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state

        try:
            # Execute the graph using pydantic-graph async
            result = await self._pydantic_graph.run(start_node, state=execution_state)

            # Extract the actual output from pydantic-graph result
            if hasattr(result, "data"):
                output = result.data
            elif hasattr(result, "output"):
                output = result.output
            else:
                output = str(result)

            # Create our response object
            return GraphResponse(
                type="graph",
                model=self._global_model or "openai/gpt-4o-mini",
                output=output,
                content=str(output),
                completion=None,
                state=execution_state,
                history=[],  # Would be populated from pydantic-graph execution
                start_node=self._start_action_name,
                nodes_executed=[self._start_action_name],  # Would track from execution
                metadata={},
            )

        except Exception as e:
            raise RuntimeError(f"Async graph execution failed: {e}") from e

    async def async_iter(
        self,
        *args,
        state: Optional[StateT] = None,
        history: Optional[AgentMessages] = None,
        verbose: bool = False,
        debug: bool = False,
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        **kwargs,
    ) -> GraphStream[T, StateT]:
        """Async version of iter.

        Args:
            *args: Arguments for the start action
            state: Optional state object to use for the execution
            history: Optional chat history in various formats (str, messages list, History object)
            verbose: Enable verbose logging
            debug: Enable debug logging
            max_steps: Maximum number of steps to execute
            end_strategy: Strategy for ending execution
            end_tool: Tool to use for ending execution
            **kwargs: Additional keyword arguments for the start action and language model

        Returns:
            GraphStream that can be iterated over asynchronously
        """

        if self._start_action_name is None:
            raise ValueError("No start action defined")

        start_node_class = self._action_nodes[self._start_action_name]
        start_sig = self._get_start_action_signature()

        # Separate language model kwargs from start action kwargs
        language_model_kwargs = {}
        start_action_kwargs = {}

        # Language model specific parameters
        lm_params = {
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "stream",
            "response_format",
            "seed",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "functions",
            "function_call",
            "user",
            "system",
            "n",
            "echo",
            "logprobs",
            "top_logprobs",
            "suffix",
            "max_retries",
            "timeout",
            "model",
            "type",
            "instructor_mode",
            "max_steps",
            "end_strategy",
            "end_tool",
        }

        for key, value in kwargs.items():
            if key in lm_params:
                language_model_kwargs[key] = value
            else:
                start_action_kwargs[key] = value

        try:
            bound_args = start_sig.bind(*args, **start_action_kwargs)
            bound_args.apply_defaults()
        except TypeError as e:
            raise ValueError(
                f"Invalid arguments for start action '{self._start_action_name}': {e}"
            )

        start_node = start_node_class(**bound_args.arguments)
        # Pass the graph docstring to the node for global system prompt
        start_node._graph_docstring = self.__class__.__doc__ or ""
        # Pass verbose/debug flags and language model kwargs
        start_node._verbose = verbose
        start_node._debug = debug
        start_node._language_model_kwargs = language_model_kwargs
        # Pass history if provided
        start_node._history = history

        # Pass end strategy parameters if provided
        if max_steps is not None:
            start_node._max_steps = max_steps
        if end_strategy is not None:
            start_node._end_strategy = end_strategy
        if end_tool is not None:
            start_node._end_tool = end_tool

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state

        # Create and return GraphStream
        return GraphStream(
            graph=self,
            start_node=start_node,
            state=execution_state,
            verbose=verbose,
            debug=debug,
            max_steps=max_steps,
            end_strategy=end_strategy,
            end_tool=end_tool,
            **language_model_kwargs,
        )

    def visualize(self, filename: str) -> None:
        """Generate a visualization of the graph using pydantic-graph's mermaid support."""
        if self._pydantic_graph and self._start_action_name:
            start_node_class = self._action_nodes.get(self._start_action_name)
            if start_node_class:
                # Use pydantic-graph's built-in mermaid generation
                mermaid_code = self._pydantic_graph.mermaid_code(
                    start_node=start_node_class
                )
                with open(filename, "w") as f:
                    f.write(mermaid_code)

    @classmethod
    def builder(cls) -> GraphBuilder[StateT, T]:
        """Create a builder for this graph."""
        return GraphBuilder(cls)
