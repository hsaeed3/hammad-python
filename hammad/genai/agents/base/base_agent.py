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
)

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
from ...language_models.language_model import (
    LanguageModel,
    LanguageModelMessagesParam
)
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


def _format_messages(
    messages : List[Dict[str, Any]],
    instructions : str | None = None,
) -> List[Dict[str, Any]]:
    """Formats the messages for an agent by consolidating the system
    message (instructions) within the agent's message thread for use
    within execution.
    """
    # Add system instructions if provided
    if instructions:
        system_message = {
            "role": "system",
            "content": instructions
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
    interface."""

    def __init__(
        self,
        name : str = "agent",
        instructions : str | None = None,
        model : LanguageModel | str = "openai/gpt-4o-mini",
        description : str | None = None,
        tools : List[Tool] | Callable | None = None,
        run_settings : BaseAgentRunSettings | None = None,
        add_name_to_instructions : bool = True,
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

    def run(
        self,
        messages : LanguageModelMessagesParam,
        model : LanguageModel | str | None = None,
        max_steps : Optional[int] = None,
        **kwargs : Any
    ) -> BaseAgentResponse[T]:
        """Runs this agent and returns a final agent response.
        
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
