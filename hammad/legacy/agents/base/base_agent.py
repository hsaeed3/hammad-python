"""hammad.genai.agents.base.base_agent"""

from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Literal,
    List,
    Type,
    TypeVar,
    Optional,
    Iterator,
    AsyncIterator,
    Union,
    Dict,
    overload,
    TYPE_CHECKING,
    ContextManager,
    AsyncContextManager,
)
from contextlib import contextmanager, asynccontextmanager
from pydantic import BaseModel, create_model
from enum import Enum
import json
import weakref
from functools import wraps

from ...language_models.language_model_response import (
    LanguageModelResponse,
)
from ...language_models.language_model_response_chunk import (
    LanguageModelResponseChunk,
)
from ...language_models._types import (
    LanguageModelName,
    LanguageModelInstructorMode
)
from ....formatting.text.converters import convert_to_text
from ...language_models.language_model import (
    LanguageModel,
    LanguageModelMessagesParam
)
from ...language_models._streaming import Stream, AsyncStream
from ...language_models._utils._completions import (
    parse_messages_input
)
from ...language_models._utils._messages import (
    consolidate_system_messages
)
from .base_agent_response import (
    BaseAgentResponse,
    _create_agent_response_from_language_model_response
)
from ._streaming import (
    BaseAgentStream,
    BaseAgentAsyncStream,
    BaseAgentResponseChunk,
)
from ..types.tool import (
    Tool,
    function_tool,
    execute_tools_from_language_model_response
)


T = TypeVar("T")
Context = TypeVar("Context", bound=Union[BaseModel, Dict[str, Any]])


# Event system types
class AgentEvent:
    """Base class for all agent events with universal event checking."""
    
    def __init__(self, event_type: str, data: Any = None, metadata: Dict[str, Any] = None):
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
    
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
    
    def __repr__(self) -> str:
        return f"AgentEvent(type='{self.event_type}', data={self.data}, metadata={self.metadata})"


class HookManager:
    """Manages hooks for agent events."""
    
    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.specific_hooks: Dict[str, Dict[str, List[Callable]]] = {}
    
    def register_hook(self, event_type: str, callback: Callable, specific_name: str = None):
        """Register a hook for an event type."""
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
    
    def trigger_hooks(self, event_type: str, data: Any, specific_name: str = None):
        """Trigger hooks for an event type."""
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


class HookDecorator:
    """Provides type-hinted hook decorators with extensible event system."""
    
    def __init__(self, hook_manager: HookManager):
        self.hook_manager = hook_manager
        self._event_types = set()
    
    def __call__(self, event_type: str, specific_name: str = None):
        """Register a hook for any event type."""
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
    
    # Dynamic event type classes - these are created dynamically
    # based on the actual events that occur in the system
    def __getattr__(self, name: str):
        """Dynamically create event type classes for better type hinting."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        # Create a dynamic class for this event type
        class DynamicEventType:
            def __init__(self, event_data: Any = None, metadata: Dict[str, Any] = None):
                self.event_data = event_data
                self.metadata = metadata or {}
            
            def __repr__(self):
                return f"{name}(data={self.event_data}, metadata={self.metadata})"
        
        DynamicEventType.__name__ = name
        DynamicEventType.__qualname__ = f"{self.__class__.__name__}.{name}"
        
        # Cache the class
        setattr(self, name, DynamicEventType)
        return DynamicEventType


def _build_tools(tools: List[Tool] | Callable | None) -> List[Tool]:
    """Builds a list of tools from a list of tools or a callable that returns a list of tools."""
    if tools is None:
        return []
    if callable(tools):
        return [function_tool(tools)]
    
    processed_tools = []
    for tool in tools:
        if not isinstance(tool, Tool):
            tool = function_tool(tool)
        processed_tools.append(tool)
    
    return processed_tools


def _get_instructions(
    name : str,
    instructions : str | None,
    add_name_to_instructions : bool,
) -> str:
    """Gets the instructions for an agent."""
    if add_name_to_instructions:
        return f"You are {name}.\n\n{instructions}"
    return instructions


def _parse_messages(
    messages : LanguageModelMessagesParam,
) -> List[Dict[str, Any]]:
    """Parses the messages for an agent."""
    return parse_messages_input(messages)


def _format_context_for_instructions(
    context: Context | None,
    context_format: Literal["json", "python", "markdown"] = "json"
) -> str:
    """Format context object for inclusion in instructions."""
    if context is None:
        return ""
    
    if context_format == "json":
        if isinstance(context, BaseModel):
            return context.model_dump_json(indent=2)
        elif isinstance(context, dict):
            return json.dumps(context, indent=2)
        else:
            return json.dumps(str(context), indent=2)
    
    elif context_format == "python":
        if hasattr(context, "__repr__"):
            return repr(context)
        elif hasattr(context, "__str__"):
            return str(context)
        else:
            return str(context)
    
    elif context_format == "markdown":
        return convert_to_text(context)
    
    return str(context)


def _update_context_object(
    context: Context,
    updates: Dict[str, Any]
) -> Context:
    """Update a context object with new values."""
    if isinstance(context, BaseModel):
        # For Pydantic models, create a copy with updated values
        return context.model_copy(update=updates)
    elif isinstance(context, dict):
        # For dictionaries, update in place
        updated_context = context.copy()
        updated_context.update(updates)
        return updated_context
    else:
        raise ValueError(f"Cannot update context of type {type(context)}")


def _format_messages(
    messages : List[Dict[str, Any]],
    instructions : str | None = None,
    context: Context | None = None,
    context_format: Literal["json", "python", "markdown"] = "json"
) -> List[Dict[str, Any]]:
    """Formats the messages for an agent by consolidating the system
    message (instructions) within the agent's message thread for use
    within execution.
    """
    # Build complete instructions
    complete_instructions = instructions or ""
    
    # Add context to instructions if provided
    if context is not None:
        context_str = _format_context_for_instructions(context, context_format)
        if context_str:
            complete_instructions += f"\n\nContext:\n{context_str}"
    
    # Add system instructions if provided
    if complete_instructions:
        system_message = {
            "role": "system",
            "content": complete_instructions
        }
        # Insert system message at the beginning
        messages = [system_message] + messages
    
    # Format and consolidate system messages
    return consolidate_system_messages(messages)


@dataclass
class BaseAgentRunSettings: 
    """Settings object that controls the default behavior of an agent's run."""

    max_steps : int = field(default=10)
    """The maximum amount of steps the agent can take before stopping."""


class BaseAgent(Generic[T]):
    """Base class defining agents within the `hammad.genai.agents` module.
    This class is not abstract and implements the very 'minimal' agentic
    interface with comprehensive context management and hook system."""

    def __init__(
        self,
        name : str = "agent",
        instructions : str | None = None,
        model : LanguageModel | str = "openai/gpt-4o-mini",
        description : str | None = None,
        tools : List[Tool] | Callable | None = None,
        run_settings : BaseAgentRunSettings | None = None,
        add_name_to_instructions : bool = True,
        # Interface 1: output_instructor_mode parameter
        output_instructor_mode: LanguageModelInstructorMode | None = None,
        # Interface 2: Context parameters
        context_updates: List[Literal["before", "after"]] | Literal["before", "after"] | None = None,
        context_confirm: bool = False,
        context_strategy: Literal["selective", "all"] = "all",
        context_max_retries: int = 3,
        context_confirm_instructions: str | None = None,
        context_selection_instructions: str | None = None,
        context_update_instructions: str | None = None,
        context_format: Literal["json", "python", "markdown"] = "json",
    ):
        self.name = name
        self.description = description
        self.add_name_to_instructions = add_name_to_instructions

        if not run_settings:
            run_settings = BaseAgentRunSettings()
        self.run_settings = run_settings

        self.tools = _build_tools(tools)
        self.instructions = _get_instructions(
            name = name,
            instructions = instructions,
            add_name_to_instructions = add_name_to_instructions,
        )

        if isinstance(model, str):
            model = LanguageModel(model=model)
        self.model = model
        
        # Interface 1: Store output_instructor_mode
        self.output_instructor_mode = output_instructor_mode
        
        # Interface 2: Context configuration
        self.context_updates = context_updates
        self.context_confirm = context_confirm
        self.context_strategy = context_strategy
        self.context_max_retries = context_max_retries
        self.context_confirm_instructions = context_confirm_instructions
        self.context_selection_instructions = context_selection_instructions
        self.context_update_instructions = context_update_instructions
        self.context_format = context_format
        
        # Hook system
        self.hook_manager = HookManager()
        self.on = HookDecorator(self.hook_manager)

    def _should_update_context(self, context: Context, timing: Literal["before", "after"]) -> bool:
        """Determine if context should be updated based on timing and configuration."""
        if not self.context_updates:
            return False
        
        if isinstance(self.context_updates, str):
            return self.context_updates == timing
        else:
            return timing in self.context_updates

    def _create_context_confirm_model(self):
        """Create IsUpdateRequired model for context confirmation."""
        return create_model(
            "IsUpdateRequired",
            decision=(bool, ...)
        )

    def _create_context_selection_model(self, context: Context):
        """Create FieldsToUpdate model for selective context updates."""
        if isinstance(context, BaseModel):
            field_names = list(context.model_fields.keys())
        elif isinstance(context, dict):
            field_names = list(context.keys())
        else:
            raise ValueError(f"Cannot create selection model for context type {type(context)}")
        
        FieldEnum = Enum("FieldEnum", {name: name for name in field_names})
        return create_model(
            "FieldsToUpdate",
            fields=(List[FieldEnum], ...)
        )

    def _create_context_update_model(self, context: Context, field_name: str = None):
        """Create update model for context updates."""
        if field_name:
            # Single field update
            if isinstance(context, BaseModel):
                field_type = context.model_fields[field_name].annotation
            elif isinstance(context, dict):
                field_type = type(context[field_name])
            else:
                field_type = Any
            
            return create_model(
                field_name.capitalize(),
                **{field_name: (field_type, ...)}
            )
        else:
            # All fields update
            return create_model(
                "Update",
                updates=(Dict[str, Any], ...)
            )

    def _perform_context_update(self, context: Context, model: LanguageModel, current_messages: List[Dict[str, Any]], timing: Literal["before", "after"]) -> Context:
        """Perform context update with retries and error handling."""
        updated_context = context
        
        for attempt in range(self.context_max_retries):
            try:
                # Check if update is needed (if confirmation is enabled)
                if self.context_confirm:
                    confirm_model = self._create_context_confirm_model()
                    confirm_instructions = f"Based on the conversation, determine if the context should be updated {timing} processing."
                    if self.context_confirm_instructions:
                        confirm_instructions += f"\n\n{self.context_confirm_instructions}"
                    
                    confirm_response = model.run(
                        messages=current_messages + [{"role": "user", "content": confirm_instructions}],
                        type=confirm_model,
                        instructor_mode=self.output_instructor_mode
                    )
                    
                    if not confirm_response.output.decision:
                        return updated_context
                
                # Perform the update based on strategy
                if self.context_strategy == "selective":
                    # Get fields to update
                    selection_model = self._create_context_selection_model(updated_context)
                    selection_instructions = f"Select which fields in the context should be updated {timing} processing."
                    if self.context_selection_instructions:
                        selection_instructions += f"\n\n{self.context_selection_instructions}"
                    
                    selection_response = model.run(
                        messages=current_messages + [{"role": "user", "content": selection_instructions}],
                        type=selection_model,
                        instructor_mode=self.output_instructor_mode
                    )
                    
                    # Update each selected field
                    for field_enum in selection_response.output.fields:
                        field_name = field_enum.value
                        field_model = self._create_context_update_model(updated_context, field_name)
                        field_instructions = f"Update the {field_name} field in the context."
                        if self.context_update_instructions:
                            field_instructions += f"\n\n{self.context_update_instructions}"
                        
                        field_response = model.run(
                            messages=current_messages + [{"role": "user", "content": field_instructions}],
                            type=field_model,
                            instructor_mode=self.output_instructor_mode
                        )
                        
                        # Apply the update
                        field_updates = {field_name: getattr(field_response.output, field_name)}
                        updated_context = _update_context_object(updated_context, field_updates)
                
                else:  # strategy == "all"
                    # Update all fields at once
                    update_model = self._create_context_update_model(updated_context)
                    update_instructions = f"Update the context {timing} processing."
                    if self.context_update_instructions:
                        update_instructions += f"\n\n{self.context_update_instructions}"
                    
                    update_response = model.run(
                        messages=current_messages + [{"role": "user", "content": update_instructions}],
                        type=update_model,
                        instructor_mode=self.output_instructor_mode
                    )
                    
                    # Apply the updates
                    updated_context = _update_context_object(updated_context, update_response.output.updates)
                
                # Trigger context update hooks
                self.hook_manager.trigger_hooks("context_update", updated_context)
                
                return updated_context
                
            except Exception as e:
                if attempt == self.context_max_retries - 1:
                    # Last attempt failed, return original context
                    return updated_context
                # Continue to next attempt
                continue
        
        return updated_context

    # Overloaded run methods for streaming support
    @overload
    def run(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        context: Context | None = None,
        output_type: Type[T] | None = None,
        *,
        stream: Literal[False] = False,
        **kwargs : Any
    ) -> BaseAgentResponse[T]: ...

    @overload
    def run(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        context: Context | None = None,
        output_type: Type[T] | None = None,
        *,
        stream: Literal[True],
        **kwargs : Any
    ) -> "BaseAgentStream[T]": ...

    def run(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        context: Context | None = None,
        output_type: Type[T] | None = None,
        stream: bool = False,
        **kwargs : Any
    ) -> Union[BaseAgentResponse[T], "BaseAgentStream[T]"]:
        """Runs this agent and returns a final agent response or stream.
        
        You can override defaults assigned to this model from
        this function directly, to use for the execution."""

        # Handle streaming
        if stream:
            return BaseAgentStream(
                agent=self,
                messages=messages,
                model=model,
                max_steps=max_steps,
                context=context,
                output_type=output_type,
                **kwargs
            )

        steps : List[LanguageModelResponse[str]] = []

        # Use provided model or default
        if model is None:
            model = self.model
        elif isinstance(model, str):
            model = LanguageModel(model=model)
        
        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.run_settings.max_steps
        
        # Parse initial messages
        parsed_messages = _parse_messages(messages)
        current_messages = parsed_messages.copy()
        
        # RUN MAIN AGENTIC LOOP
        for step in range(max_steps):
            # Format messages with instructions for first step only
            if step == 0:
                formatted_messages = _format_messages(
                    messages = current_messages,
                    instructions = self.instructions,
                )
            else:
                formatted_messages = current_messages
            
            # Get language model response
            response = model.run(
                messages = formatted_messages,
                tools = [tool.to_dict() for tool in self.tools] if self.tools else None,
                **kwargs
            )
            
            # Check if response has tool calls
            if response.has_tool_calls():
                # Add response to message history (with tool calls)
                current_messages.append(response.to_message())
                
                # Execute tools and add their responses to messages
                tool_responses = execute_tools_from_language_model_response(
                    tools = self.tools,
                    response = response
                )
                # Add tool responses to message history
                for tool_resp in tool_responses:
                    current_messages.append(tool_resp.to_dict())
                
                # This is not the final step, add to steps
                steps.append(response)
            else:
                # No tool calls - this is the final step
                return _create_agent_response_from_language_model_response(
                    response = response,
                    steps = steps
                )
        
        # Max steps reached - return last response
        if steps:
            final_response = steps[-1]
        else:
            # No steps taken, make a final call
            final_response = model.run(
                messages = _format_messages(
                    messages = current_messages,
                    instructions = self.instructions,
                ),
                **kwargs
            )
        
        return _create_agent_response_from_language_model_response(
            response = final_response,
            steps = steps
        )
    
    async def async_run(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        **kwargs : Any
    ) -> BaseAgentResponse[T]:
        """Runs this agent asynchronously and returns a final agent response.
        
        You can override defaults assigned to this model from
        this function directly, to use for the execution."""
        
        steps : List[LanguageModelResponse[str]] = []
        
        # Use provided model or default
        if model is None:
            model = self.model
        elif isinstance(model, str):
            model = LanguageModel(model=model)
        
        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.run_settings.max_steps
        
        # Parse initial messages
        parsed_messages = _parse_messages(messages)
        current_messages = parsed_messages.copy()
        
        # RUN MAIN AGENTIC LOOP
        for step in range(max_steps):
            # Format messages with instructions for first step only
            if step == 0:
                formatted_messages = _format_messages(
                    messages = current_messages,
                    instructions = self.instructions,
                )
            else:
                formatted_messages = current_messages
            
            # Get language model response
            response = await model.async_run(
                messages = formatted_messages,
                tools = [tool.to_dict() for tool in self.tools] if self.tools else None,
                **kwargs
            )
            
            # Check if response has tool calls
            if response.has_tool_calls():
                # Add response to message history (with tool calls)
                current_messages.append(response.to_message())
                
                # Execute tools and add their responses to messages
                tool_responses = execute_tools_from_language_model_response(
                    tools = self.tools,
                    response = response
                )
                # Add tool responses to message history
                for tool_resp in tool_responses:
                    current_messages.append(tool_resp.to_dict())
                
                # This is not the final step, add to steps
                steps.append(response)
            else:
                # No tool calls - this is the final step
                return _create_agent_response_from_language_model_response(
                    response = response,
                    steps = steps
                )
        
        # Max steps reached - return last response
        if steps:
            final_response = steps[-1]
        else:
            # No steps taken, make a final call
            final_response = await model.async_run(
                messages = _format_messages(
                    messages = current_messages,
                    instructions = self.instructions,
                ),
                **kwargs
            )
        
        return _create_agent_response_from_language_model_response(
            response = final_response,
            steps = steps
        )
    
    def iter(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        **kwargs : Any
    ) -> "BaseAgentStream[T]":
        """Iterate over agent steps, yielding each step response."""
        
        # Use provided model or default
        if model is None:
            model = self.model
        elif isinstance(model, str):
            model = LanguageModel(model=model)
        
        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.run_settings.max_steps
        
        return BaseAgentStream(
            agent = self,
            messages = messages,
            model = model,
            max_steps = max_steps,
            **kwargs
        )
    
    def async_iter(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        **kwargs : Any
    ) -> "BaseAgentAsyncStream[T]":
        """Async iterate over agent steps, yielding each step response."""
        
        # Use provided model or default
        if model is None:
            model = self.model
        elif isinstance(model, str):
            model = LanguageModel(model=model)
        
        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.run_settings.max_steps
        
        return BaseAgentAsyncStream(
            agent = self,
            messages = messages,
            model = model,
            max_steps = max_steps,
            **kwargs
        )
