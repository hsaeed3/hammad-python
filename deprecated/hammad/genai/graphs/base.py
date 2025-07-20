"""hammad.genai.graphs.base"""

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
    TypeAlias,
    Awaitable,
    TYPE_CHECKING,
)
from typing_extensions import Literal
from dataclasses import dataclass, field
import inspect
from functools import wraps
import asyncio

from pydantic_graph import BaseNode, End, Graph as PydanticGraph, GraphRunContext
from ..models.language.utils import (
    parse_messages_input,
    consolidate_system_messages,
)
from ...formatting.text import convert_to_text

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
from ._utils import visualize_base_graph

if TYPE_CHECKING:
    try:
        from fasta2a import FastA2A
    except ImportError:
        FastA2A: TypeAlias = Any

__all__ = [
    "BaseGraph",
    "action",
    "ActionNode",
    "GraphBuilder",
    "GraphStream",
    "GraphResponseChunk",
    "select",
    "SelectionStrategy",
]

T = TypeVar("T")
StateT = TypeVar("StateT")
P = ParamSpec("P")


class SelectionStrategy:
    """LLM-based selection strategy for choosing the next action."""

    def __init__(
        self,
        *actions: str,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.actions = list(actions)
        self.instructions = instructions
        self.model = model or "openai/gpt-4o-mini"
        self._language_model = None
        self._use_all_actions = (
            len(actions) == 0
        )  # If no actions specified, use all available

    def _get_language_model(self):
        """Lazy load the language model."""
        if self._language_model is None:
            from ..models.language.model import LanguageModel

            self._language_model = LanguageModel(model=self.model)
        return self._language_model

    def select(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to select the most appropriate action."""
        if not context:
            context = {}

        # Get available actions
        actions_to_choose_from = self.actions
        if self._use_all_actions and "all_actions" in context:
            # Use all available actions from the graph
            actions_to_choose_from = context["all_actions"]

        if not actions_to_choose_from:
            return ""

        # If only one action, return it
        if len(actions_to_choose_from) == 1:
            return actions_to_choose_from[0]

        # Import here to avoid circular imports
        from pydantic import BaseModel, Field, create_model
        from enum import Enum

        # Create enum for available actions
        ActionEnum = Enum(
            "ActionEnum", {action: action for action in actions_to_choose_from}
        )

        # Create selection model
        SelectionModel = create_model(
            "ActionSelection",
            action=(
                ActionEnum,
                Field(description="The selected action to execute next"),
            ),
            reasoning=(str, Field(description="Brief reasoning for the selection")),
        )

        # Build context description
        context_parts = []

        # Add result from previous action
        if "result" in context:
            context_parts.append(f"Previous action result: {context['result']}")

        # Add conversation history
        if "messages" in context and context["messages"]:
            # Get last few messages for context
            recent_messages = context["messages"][-5:]  # Last 5 messages
            messages_str = "\n".join(
                [
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in recent_messages
                ]
            )
            context_parts.append(f"Recent conversation:\n{messages_str}")

        # Add state information
        if "state" in context and context["state"]:
            context_parts.append(f"Current state: {context['state']}")

        context_description = "\n\n".join(context_parts)

        # Build selection prompt
        base_instructions = f"""Based on the context below, select the most appropriate next action from the available options.

Available actions:
{", ".join(actions_to_choose_from)}

Context:
{context_description}

Consider the conversation flow, user's request, and any patterns in the conversation when making your selection.
For example, if the user asked to do something multiple times (e.g., "reason twice"), and you've only done it once, select that action again."""

        # Add custom instructions if provided
        if self.instructions:
            base_instructions = (
                f"{base_instructions}\n\nAdditional instructions:\n{self.instructions}"
            )

        # Get language model to make selection
        try:
            lm = self._get_language_model()
            response = lm.run(
                messages=[{"role": "user", "content": base_instructions}],
                type=SelectionModel,
            )

            selected_action = response.output.action.value

            # Validate the selection
            if selected_action in actions_to_choose_from:
                return selected_action
            else:
                # Fallback to first action if invalid selection
                return actions_to_choose_from[0]

        except Exception:
            # Fallback to first action on any error
            return actions_to_choose_from[0] if actions_to_choose_from else ""

    def __repr__(self) -> str:
        if self._use_all_actions:
            return f"SelectionStrategy(all_actions)"
        return f"SelectionStrategy({', '.join(repr(a) for a in self.actions)})"

    def select(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to select the most appropriate action."""
        if not context or not self.actions:
            return self.actions[0] if self.actions else ""

        # Import here to avoid circular imports
        from pydantic import BaseModel, Field, create_model
        from enum import Enum

        # Create enum for available actions
        ActionEnum = Enum("ActionEnum", {action: action for action in self.actions})

        # Create selection model
        SelectionModel = create_model(
            "ActionSelection",
            action=(
                ActionEnum,
                Field(description="The selected action to execute next"),
            ),
            reasoning=(str, Field(description="Brief reasoning for the selection")),
        )

        # Build context description
        context_parts = []

        # Add result from previous action
        if "result" in context:
            context_parts.append(f"Previous action result: {context['result']}")

        # Add conversation history
        if "messages" in context and context["messages"]:
            # Get last few messages for context
            recent_messages = context["messages"][-5:]  # Last 5 messages
            messages_str = "\n".join(
                [
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in recent_messages
                ]
            )
            context_parts.append(f"Recent conversation:\n{messages_str}")

        # Add state information
        if "state" in context and context["state"]:
            context_parts.append(f"Current state: {context['state']}")

        context_description = "\n\n".join(context_parts)

        # Build selection prompt
        base_instructions = f"""Based on the context below, select the most appropriate next action from the available options.

Available actions:
{", ".join(self.actions)}

Context:
{context_description}

Consider the conversation flow and any specific instructions from the user when making your selection."""

        # Add custom instructions if provided
        if self.instructions:
            base_instructions = (
                f"{base_instructions}\n\nAdditional instructions:\n{self.instructions}"
            )

        # Get language model to make selection
        try:
            lm = self._get_language_model()
            response = lm.run(
                messages=[{"role": "user", "content": base_instructions}],
                type=SelectionModel,
            )

            selected_action = response.output.action.value

            # Validate the selection
            if selected_action in self.actions:
                return selected_action
            else:
                # Fallback to first action if invalid selection
                return self.actions[0]

        except Exception:
            # Fallback to first action on any error
            return self.actions[0] if self.actions else ""


def select(
    *actions: str, instructions: Optional[str] = None, model: Optional[str] = None
) -> SelectionStrategy:
    """
    Create an LLM-based selection strategy for choosing between multiple actions.

    Args:
        *actions: The action names to choose from. If empty, will select from all available actions.
        instructions: Optional instructions for the LLM selection
        model: Optional model to use for selection (defaults to gpt-4o-mini)

    Returns:
        A SelectionStrategy instance

    Examples:
        # Select between specific actions
        @action(next=select("poem", "response"))
        def reasoning(self, message: str) -> str:
            ...

        # Select from all available actions in the graph
        @action(next=select())
        def reasoning(self, message: str) -> str:
            ...

        # With custom instructions
        @action(next=select("reasoning", "response",
                          instructions="If the user asked for multiple reasonings, select 'reasoning' again"))
        def reasoning(self, message: str) -> str:
            ...
    """
    return SelectionStrategy(*actions, instructions=instructions, model=model)


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

        # Track this node's execution
        execution_tracker = getattr(self, "_execution_tracker", [])
        execution_tracker.append(self.action_name)

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

        # Get state from the context if available
        current_state = None
        if hasattr(ctx, "state") and ctx.state is not None:
            current_state = ctx.state
        elif hasattr(self, "_state"):
            current_state = getattr(self, "_state", None)

        # Check if the action function expects to handle the language model itself
        expects_language_model = (
            "language_model" in sig.parameters or "agent" in sig.parameters
        )

        if expects_language_model:
            # Legacy mode: action function expects to handle language model
            # Combine global system prompt with field-level instructions and state
            combined_instructions = global_system_prompt
            if field_instructions and field_instructions not in combined_instructions:
                if combined_instructions:
                    combined_instructions += f"\n\n{field_instructions}"
                else:
                    combined_instructions = field_instructions

            # Add state to instructions if available
            if current_state is not None:
                state_str = convert_to_text(current_state, show_defaults=False)
                if state_str:
                    combined_instructions += f"\n\nState: {state_str}"

            # Get verbose/debug flags and language model kwargs from the node
            verbose = getattr(self, "_verbose", self.settings.verbose)
            debug = getattr(self, "_debug", self.settings.debug)
            language_model_kwargs = getattr(self, "_language_model_kwargs", {})

            # Get end strategy parameters from node or settings
            max_steps = getattr(self, "_max_steps", self.settings.max_steps)
            end_strategy = getattr(self, "_end_strategy", self.settings.end_strategy)
            end_tool = getattr(self, "_end_tool", self.settings.end_tool)

            if self.settings.tools or self.settings.instructions:
                # Get model from settings, then language_model_kwargs, then default
                model = self.settings.model or language_model_kwargs.get(
                    "model", "openai/gpt-4o-mini"
                )

                # Remove parameters that will be passed explicitly to avoid duplicates
                filtered_kwargs = {
                    k: v
                    for k, v in language_model_kwargs.items()
                    if k
                    not in [
                        "model",
                        "name",
                        "instructions",
                        "tools",
                        "max_steps",
                        "end_strategy",
                        "end_tool",
                        "verbose",
                        "debug",
                    ]
                }

                agent = Agent(
                    name=self.settings.name or self.action_name,
                    instructions=self.settings.instructions or combined_instructions,
                    model=model,
                    tools=self.settings.tools,
                    max_steps=max_steps,
                    end_strategy=end_strategy,
                    end_tool=end_tool,
                    verbose=verbose,
                    debug=debug,
                    **filtered_kwargs,
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
                # Get model from settings, then language_model_kwargs, then default
                model = self.settings.model or language_model_kwargs.get(
                    "model", "openai/gpt-4o-mini"
                )

                # Remove parameters that will be passed explicitly to avoid duplicates
                filtered_kwargs = {
                    k: v
                    for k, v in language_model_kwargs.items()
                    if k not in ["model", "verbose", "debug"]
                }

                language_model = LanguageModel(
                    model=model,
                    verbose=verbose,
                    debug=debug,
                    **filtered_kwargs,
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
            # Build the user message from the action parameters
            user_message = ""
            if action_params:
                if len(action_params) == 1:
                    # Single parameter - use its value directly
                    param_value = list(action_params.values())[0]
                    user_message = str(param_value)
                else:
                    # Multiple parameters - format them clearly
                    param_list = "\n".join(
                        f"{k}: {v}" for k, v in action_params.items()
                    )
                    user_message = param_list
            else:
                # No parameters - check if we have previous conversation history
                # If we do, don't add an empty user message
                user_message = ""

            # Combine global system prompt with field-level instructions and state
            combined_instructions = global_system_prompt
            if field_instructions and field_instructions not in combined_instructions:
                if combined_instructions:
                    combined_instructions += f"\n\n{field_instructions}"
                else:
                    combined_instructions = field_instructions

            # Add state to instructions if available
            if current_state is not None:
                state_str = convert_to_text(current_state, show_defaults=False)
                if state_str:
                    combined_instructions += f"\n\nContext: {state_str}"

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
                # Get model from settings, then language_model_kwargs, then default
                model = self.settings.model or language_model_kwargs.get(
                    "model", "openai/gpt-4o-mini"
                )

                # Remove parameters that will be passed explicitly to avoid duplicates
                filtered_kwargs = {
                    k: v
                    for k, v in language_model_kwargs.items()
                    if k
                    not in [
                        "model",
                        "name",
                        "instructions",
                        "tools",
                        "max_steps",
                        "end_strategy",
                        "end_tool",
                        "verbose",
                        "debug",
                    ]
                }

                agent = Agent(
                    name=self.settings.name or self.action_name,
                    instructions=self.settings.instructions or combined_instructions,
                    model=model,
                    tools=self.settings.tools,
                    max_steps=max_steps,
                    end_strategy=end_strategy,
                    end_tool=end_tool,
                    verbose=verbose,
                    debug=debug,
                    **filtered_kwargs,
                )

                # Get history if available
                history = getattr(self, "_history", None)

                # Check if we have previous conversation history from the graph execution
                previous_messages = getattr(self, "_graph_messages", [])

                # Store the current user message for history building
                if user_message:
                    self._current_user_message = user_message

                # Run the agent with the user message and history
                if history:
                    # If history is provided, we need to combine it with the user message
                    # The history should be the conversation context, and user_message is the new input
                    combined_messages = parse_messages_input(history)
                    combined_messages.extend(previous_messages)
                    if user_message:  # Only add non-empty user messages
                        combined_messages.append(
                            {"role": "user", "content": user_message}
                        )
                    agent_result = await agent.async_run(combined_messages)
                elif previous_messages:
                    # If we have previous messages from the graph, use them
                    combined_messages = previous_messages.copy()
                    if user_message:  # Only add non-empty user messages
                        combined_messages.append(
                            {"role": "user", "content": user_message}
                        )
                    agent_result = await agent.async_run(combined_messages)
                else:
                    # Only run with user message if it's not empty
                    if user_message:
                        agent_result = await agent.async_run(user_message)
                    else:
                        # If no user message and no history, we can't run the agent
                        raise ValueError(
                            "No user message or history provided for agent execution"
                        )
                result = agent_result.output
            else:
                # Use LanguageModel for simple operations
                # Get model from settings, then language_model_kwargs, then default
                model = self.settings.model or language_model_kwargs.get(
                    "model", "openai/gpt-4o-mini"
                )

                # Remove parameters that will be passed explicitly to avoid duplicates
                filtered_kwargs = {
                    k: v
                    for k, v in language_model_kwargs.items()
                    if k not in ["model", "verbose", "debug"]
                }

                language_model = LanguageModel(
                    model=model,
                    verbose=verbose,
                    debug=debug,
                    **filtered_kwargs,
                )

                # Get history if available
                history = getattr(self, "_history", None)

                # Check if we have previous conversation history from the graph execution
                previous_messages = getattr(self, "_graph_messages", [])

                # Create messages using the language model utils
                if history:
                    # If history is provided, use it as the base messages
                    messages = parse_messages_input(
                        history, instructions=combined_instructions
                    )
                    # Add any previous graph messages
                    messages.extend(previous_messages)
                    # Then add the user message from action parameters
                    if user_message:  # Only add non-empty user messages
                        messages.append({"role": "user", "content": user_message})
                elif previous_messages:
                    # If we have previous messages from the graph, use them
                    messages = parse_messages_input(
                        "", instructions=combined_instructions
                    )
                    messages.extend(previous_messages)
                    if user_message:  # Only add non-empty user messages
                        messages.append({"role": "user", "content": user_message})
                else:
                    # Otherwise, use the user message (if not empty)
                    if user_message:
                        messages = parse_messages_input(
                            user_message, instructions=combined_instructions
                        )
                    else:
                        # If no user message and no history, just use instructions
                        messages = parse_messages_input(
                            "", instructions=combined_instructions
                        )
                messages = consolidate_system_messages(messages)

                # Store the current user message for history building
                if user_message:
                    self._current_user_message = user_message

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
            # Check if there's a next action defined
            if self.settings.next:
                # Handle different types of next specifications
                next_action_name = None

                if isinstance(self.settings.next, str):
                    # Simple string case
                    next_action_name = self.settings.next
                elif isinstance(self.settings.next, list):
                    # List case - for now, just pick the first one
                    # In the future, this could execute all in parallel
                    if self.settings.next:
                        next_action_name = self.settings.next[0]
                elif isinstance(self.settings.next, SelectionStrategy):
                    # Selection strategy case - use the strategy to pick an action
                    context = {
                        "result": result,
                        "state": getattr(self, "_state", None),
                        "messages": getattr(self, "_graph_messages", []),
                    }
                    # If using all actions, pass them in the context
                    if self.settings.next._use_all_actions and hasattr(
                        self, "_graph_action_nodes"
                    ):
                        context["all_actions"] = list(self._graph_action_nodes.keys())
                    next_action_name = self.settings.next.select(context)
                else:
                    # Invalid type for next
                    return End(result)

                # Find the next node class from the graph's action nodes
                if hasattr(self, "_graph_action_nodes") and next_action_name:
                    next_node_class = self._graph_action_nodes.get(next_action_name)
                    if next_node_class:
                        # Create the next node instance
                        # For graph flow, we don't pass the result as a parameter
                        # The conversation history will contain the context
                        next_node = next_node_class()

                        # Copy over any graph-specific attributes
                        for attr in [
                            "_graph_docstring",
                            "_verbose",
                            "_debug",
                            "_language_model_kwargs",
                            "_history",
                            "_state",
                            "_graph_action_nodes",
                            "_execution_tracker",
                        ]:
                            if hasattr(self, attr):
                                setattr(next_node, attr, getattr(self, attr))

                        # Build up the conversation history for the next node
                        current_messages = getattr(self, "_graph_messages", [])
                        # Add the current interaction to the conversation history
                        # Only add the user message if it was actually provided (not empty)
                        if (
                            hasattr(self, "_current_user_message")
                            and self._current_user_message
                        ):
                            current_messages.append(
                                {"role": "user", "content": self._current_user_message}
                            )
                        # Add the assistant response from this node
                        current_messages.append(
                            {"role": "assistant", "content": str(result)}
                        )
                        next_node._graph_messages = current_messages

                        return next_node

                # If we can't find any valid next node, terminate
                return End(result)
            else:
                # No next action defined, terminate
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
        next: Optional[Union[str, List[str], SelectionStrategy]] = None,
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
            
            # Check if action name is reserved
            reserved_names = {
                'run', 'async_run', 'iter', 'async_iter', 
                'visualize', 'builder', 'as_a2a',
                '_initialize', '_collect_state_class', '_collect_actions',
                '_create_pydantic_graph', '_get_start_action_signature'
            }
            if action_name in reserved_names:
                raise ValueError(
                    f"Action name '{action_name}' is reserved and cannot be used. "
                    f"Reserved names include: {', '.join(sorted(reserved_names))}. "
                    "Please choose a different name for your action."
                )
            
            # Check that the action has at least one parameter besides 'self'
            sig = inspect.signature(f)
            params = [p for p in sig.parameters if p != 'self']
            if not params:
                raise ValueError(
                    f"Action '{action_name}' must have at least one parameter besides 'self'. "
                    "Actions need input parameters to process."
                )

            # Create a dynamic ActionNode class for this specific action with unique name
            class DynamicActionNode(ActionNode[StateT]):
                def __init__(self, **action_params):
                    super().__init__(
                        action_name=action_name,
                        action_func=f,
                        settings=settings,
                        **action_params,
                    )

                @classmethod
                def get_node_id(cls):
                    """Override to provide unique node ID based on action name."""
                    return f"DynamicActionNode_{action_name}"

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

    def __init__(
        self,
        state: Optional[StateT] = None,
        *,
        model: Optional[LanguageModelName | str] = "openai/gpt-4.1-nano",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Callable]] = None,
        verbose: bool = False,
        debug: bool = False,
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        summarize_tools: bool = True,
        summarize_tools_with_model: bool = False,
        plugins: Optional[List[BasePlugin]] = None,
        **kwargs: Any,
    ):
        self._plugins: List[BasePlugin] = plugins or []
        self._global_model: Optional[LanguageModelName] = model
        self._global_settings: Dict[str, Any] = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "verbose": verbose,
            "debug": debug,
            "max_steps": max_steps,
            "end_strategy": end_strategy,
            "end_tool": end_tool,
            "summarize_tools": summarize_tools,
            "summarize_tools_with_model": summarize_tools_with_model,
            **kwargs,
        }
        # Remove None values from settings
        self._global_settings = {
            k: v for k, v in self._global_settings.items() if v is not None
        }

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
        start_action = None
        end_action = None

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
                    start_action = attr

                # Check if this is an end action (terminates=True)
                if (
                    hasattr(attr, "_action_settings")
                    and attr._action_settings.terminates
                ):
                    end_action = attr

        # If no explicit start action was defined and we have exactly one action,
        # automatically make it the start action
        if self._start_action_name is None and len(actions_found) == 1:
            action_name, action_func = actions_found[0]
            self._start_action_name = action_name
            self._start_action_func = action_func

        # Special case: If we have exactly 2 actions (start -> end), automatically set up routing
        if len(actions_found) == 2 and start_action and end_action:
            # Check if the start action doesn't already have a 'next' defined
            if start_action._action_settings.next is None:
                # Automatically set the start action to route to the end action
                start_action._action_settings.next = end_action._action_name

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

        # Merge global settings with provided kwargs
        merged_settings = self._global_settings.copy()
        merged_settings.update(language_model_kwargs)
        
        # Include the global model if it's set and not overridden
        if self._global_model and "model" not in merged_settings:
            merged_settings["model"] = self._global_model

        # Pass verbose/debug flags (prefer explicit params over global settings)
        start_node._verbose = (
            verbose if verbose else merged_settings.get("verbose", False)
        )
        start_node._debug = debug if debug else merged_settings.get("debug", False)
        start_node._language_model_kwargs = merged_settings

        # Pass history if provided
        start_node._history = history
        # Pass the graph's action nodes for routing
        start_node._graph_action_nodes = self._action_nodes

        # Initialize execution tracking
        self._execution_tracker = []
        start_node._execution_tracker = self._execution_tracker

        # Pass end strategy parameters (from merged settings)
        if "max_steps" in merged_settings:
            start_node._max_steps = merged_settings["max_steps"]
        if "end_strategy" in merged_settings:
            start_node._end_strategy = merged_settings["end_strategy"]
        if "end_tool" in merged_settings:
            start_node._end_tool = merged_settings["end_tool"]

        # Run the pydantic graph
        if not self._pydantic_graph:
            raise ValueError("Graph not initialized")

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state
        # Pass state to the node
        start_node._state = execution_state

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

            # Get nodes executed from the execution tracker
            nodes_executed = getattr(self, "_execution_tracker", [])

            # If no nodes tracked, at least include the start node
            if not nodes_executed:
                nodes_executed = [self._start_action_name]

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
                nodes_executed=nodes_executed,
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

        # Merge global settings with provided kwargs
        merged_settings = self._global_settings.copy()
        merged_settings.update(language_model_kwargs)
        
        # Include the global model if it's set and not overridden
        if self._global_model and "model" not in merged_settings:
            merged_settings["model"] = self._global_model

        # Pass verbose/debug flags (prefer explicit params over global settings)
        start_node._verbose = (
            verbose if verbose else merged_settings.get("verbose", False)
        )
        start_node._debug = debug if debug else merged_settings.get("debug", False)
        start_node._language_model_kwargs = merged_settings

        # Pass history if provided
        start_node._history = history
        # Pass the graph's action nodes for routing
        start_node._graph_action_nodes = self._action_nodes

        # Pass end strategy parameters (prefer explicit params over merged settings)
        start_node._max_steps = (
            max_steps if max_steps is not None else merged_settings.get("max_steps")
        )
        start_node._end_strategy = (
            end_strategy
            if end_strategy is not None
            else merged_settings.get("end_strategy")
        )
        start_node._end_tool = (
            end_tool if end_tool is not None else merged_settings.get("end_tool")
        )

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state
        # Pass state to the node
        start_node._state = execution_state

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

        # Merge global settings with provided kwargs
        merged_settings = self._global_settings.copy()
        merged_settings.update(language_model_kwargs)
        
        # Include the global model if it's set and not overridden
        if self._global_model and "model" not in merged_settings:
            merged_settings["model"] = self._global_model

        # Pass verbose/debug flags (prefer explicit params over global settings)
        start_node._verbose = (
            verbose if verbose else merged_settings.get("verbose", False)
        )
        start_node._debug = debug if debug else merged_settings.get("debug", False)
        start_node._language_model_kwargs = merged_settings

        # Pass history if provided
        start_node._history = history
        # Pass the graph's action nodes for routing
        start_node._graph_action_nodes = self._action_nodes

        # Initialize execution tracking
        self._execution_tracker = []
        start_node._execution_tracker = self._execution_tracker

        # Pass end strategy parameters (prefer explicit params over merged settings)
        start_node._max_steps = (
            max_steps if max_steps is not None else merged_settings.get("max_steps")
        )
        start_node._end_strategy = (
            end_strategy
            if end_strategy is not None
            else merged_settings.get("end_strategy")
        )
        start_node._end_tool = (
            end_tool if end_tool is not None else merged_settings.get("end_tool")
        )

        # Run the pydantic graph asynchronously
        if not self._pydantic_graph:
            raise ValueError("Graph not initialized")

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state
        # Pass state to the node
        start_node._state = execution_state

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

            # Get nodes executed from the execution tracker
            nodes_executed = getattr(self, "_execution_tracker", [])

            # If no nodes tracked, at least include the start node
            if not nodes_executed:
                nodes_executed = [self._start_action_name]

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
                nodes_executed=nodes_executed,
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

        # Merge global settings with provided kwargs
        merged_settings = self._global_settings.copy()
        merged_settings.update(language_model_kwargs)
        
        # Include the global model if it's set and not overridden
        if self._global_model and "model" not in merged_settings:
            merged_settings["model"] = self._global_model

        # Pass verbose/debug flags (prefer explicit params over global settings)
        start_node._verbose = (
            verbose if verbose else merged_settings.get("verbose", False)
        )
        start_node._debug = debug if debug else merged_settings.get("debug", False)
        start_node._language_model_kwargs = merged_settings

        # Pass history if provided
        start_node._history = history
        # Pass the graph's action nodes for routing
        start_node._graph_action_nodes = self._action_nodes

        # Pass end strategy parameters (prefer explicit params over merged settings)
        start_node._max_steps = (
            max_steps if max_steps is not None else merged_settings.get("max_steps")
        )
        start_node._end_strategy = (
            end_strategy
            if end_strategy is not None
            else merged_settings.get("end_strategy")
        )
        start_node._end_tool = (
            end_tool if end_tool is not None else merged_settings.get("end_tool")
        )

        # Use the provided state or the graph's state
        execution_state = state if state is not None else self._state
        # Pass state to the node
        start_node._state = execution_state

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

    @classmethod
    def builder(cls) -> GraphBuilder[StateT, T]:
        """Create a builder for this graph."""
        return GraphBuilder(cls)

    def as_a2a(
        self,
        *,
        # Worker configuration
        state: Optional[StateT] = None,
        # Storage and broker configuration
        storage: Optional[Any] = None,
        broker: Optional[Any] = None,
        # Server configuration
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False,
        workers: int = 1,
        log_level: str = "info",
        # A2A configuration
        name: Optional[str] = None,
        url: Optional[str] = None,
        version: str = "1.0.0",
        description: Optional[str] = None,
        # Advanced configuration
        lifespan_timeout: int = 30,
        **uvicorn_kwargs: Any,
    ) -> "FastA2A":  # type: ignore
        """
        Convert this graph to an A2A server application.

        This method creates a FastA2A server that can handle A2A requests
        for this graph instance. It sets up the necessary Worker, Storage,
        and Broker components automatically.

        Args:
            state: Initial state for the graph (overrides instance state)
            storage: Custom storage backend (defaults to InMemoryStorage)
            broker: Custom broker backend (defaults to InMemoryBroker)
            host: Host to bind the server to
            port: Port to bind the server to
            reload: Enable auto-reload for development
            workers: Number of worker processes
            log_level: Logging level
            name: Graph name for the A2A server
            url: URL where the graph is hosted
            version: API version
            description: API description for the A2A server
            lifespan_timeout: Timeout for lifespan events
            **uvicorn_kwargs: Additional arguments passed to uvicorn

        Returns:
            FastA2A application instance that can be run with uvicorn

        Examples:
            Convert graph to A2A server:
            ```python
            class MyGraph(BaseGraph):
                @action.start()
                def process(self, message: str) -> str:
                    return f"Processed: {message}"

            graph = MyGraph()
            app = graph.as_a2a(port=8080)

            # Run with uvicorn
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8080)
            ```

            Or use the CLI:
            ```bash
            uvicorn mymodule:graph.as_a2a() --reload
            ```
        """
        from ..a2a import as_a2a_app

        return as_a2a_app(
            self,
            state=state if state is not None else self._state,
            storage=storage,
            broker=broker,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level=log_level,
            name=name or self.__class__.__name__,
            url=url,
            version=version,
            description=description or self.__class__.__doc__,
            lifespan_timeout=lifespan_timeout,
            **uvicorn_kwargs,
        )

    def visualize(self, filename: str) -> None:
        """Visualize the graph as mermaid.

        Args:
            filename: The filename to save the visualization to.

            Ex: 'graph.png' / 'graph.mmd'

        Returns:
            None

        """
        visualize_base_graph(self, filename)