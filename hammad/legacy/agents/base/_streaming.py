"""hammad.genai.agents.base._streaming"""

from typing import (
    Generic,
    TypeVar,
    Iterator,
    AsyncIterator,
    List,
    Any,
    Dict,
    Optional,
    TYPE_CHECKING,
    Type,
    Union,
    Literal,
)
from contextlib import contextmanager, asynccontextmanager

from ...language_models.language_model import LanguageModel, LanguageModelMessagesParam
from ...language_models.language_model_response import LanguageModelResponse
from ...language_models.language_model_response_chunk import LanguageModelResponseChunk
from ...language_models._streaming import Stream, AsyncStream
from ...language_models._utils._completions import parse_messages_input
from ...language_models._utils._messages import consolidate_system_messages
from .base_agent_response import BaseAgentResponse, _create_agent_response_from_language_model_response
from ..types.tool import execute_tools_from_language_model_response

if TYPE_CHECKING:
    from .base_agent import BaseAgent

T = TypeVar("T")


class BaseAgentResponseChunk(LanguageModelResponseChunk[T], Generic[T]):
    """A chunk from an agent response stream representing a single step."""
    
    def __init__(
        self,
        step_number: int,
        response: LanguageModelResponse[str],
        output: T | None = None,
        content: str | None = None,
        model: str | None = None,
        is_final: bool = False,
        **kwargs: Any
    ):
        """Initialize a BaseAgentResponseChunk.
        
        Args:
            step_number: The step number of this chunk
            response: The language model response for this step
            output: The output value
            content: The content string
            model: The model name
            is_final: Whether this is the final chunk
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            output=output or response.output,
            content=content or response.content,
            model=model or response.model,
            is_final=is_final,
            **kwargs
        )
        self.step_number = step_number
        self.response = response
    
    def __bool__(self) -> bool:
        """Check if this chunk has meaningful content."""
        return bool(self.response)
    
    def __str__(self) -> str:
        """String representation of the chunk."""
        return f"BaseAgentResponseChunk(step={self.step_number}, final={self.is_final})"


class BaseAgentStream(Generic[T]):
    """Stream of agent responses for iter() method that works as a context manager."""
    
    def __init__(
        self,
        agent: "BaseAgent[T]",
        messages: LanguageModelMessagesParam,
        model: LanguageModel | str | None = None,
        max_steps: int | None = None,
        context: Any = None,
        output_type: Type[T] | None = None,
        stream: bool = False,
        **kwargs: Any
    ):
        """Initialize the BaseAgentStream.
        
        Args:
            agent: The agent instance
            messages: The messages to process
            model: The language model to use
            max_steps: Maximum number of steps
            context: Context object for agent execution
            output_type: Output type for structured responses
            stream: Whether to enable streaming at language model level
            **kwargs: Additional keyword arguments for model.run()
        """
        self.agent = agent
        self.messages = messages
        self.context = context
        self.output_type = output_type
        self.stream = stream
        self.kwargs = kwargs
        self.current_step = 0
        self.steps: List[LanguageModelResponse[str]] = []
        self.current_messages = self._parse_initial_messages(messages)
        self.is_done = False
        
        # Use provided model or default
        if model is None:
            self.model = agent.model
        elif isinstance(model, str):
            self.model = LanguageModel(model=model)
        else:
            self.model = model
        
        # Use provided max_steps or default
        if max_steps is None:
            self.max_steps = agent.run_settings.max_steps
        else:
            self.max_steps = max_steps
        
        # Context handling
        self.current_context = context
        
        # Set up kwargs for model calls
        self.model_kwargs = kwargs.copy()
        if output_type:
            self.model_kwargs["type"] = output_type
        if agent.output_instructor_mode:
            self.model_kwargs["instructor_mode"] = agent.output_instructor_mode
        if stream:
            self.model_kwargs["stream"] = stream
    
    def _parse_initial_messages(self, messages: LanguageModelMessagesParam) -> List[Dict[str, Any]]:
        """Parse initial messages into a list of message dicts."""
        return parse_messages_input(messages)
    
    def _format_messages(
        self, 
        messages: List[Dict[str, Any]], 
        instructions: str | None = None
    ) -> List[Dict[str, Any]]:
        """Format messages with instructions."""
        if instructions:
            system_message = {
                "role": "system",
                "content": instructions
            }
            messages = [system_message] + messages
        return consolidate_system_messages(messages)
    
    def __enter__(self) -> "BaseAgentStream[T]":
        """Enter the context manager."""
        # Handle context updates before processing
        if self.current_context is not None and self.agent._should_update_context(self.current_context, "before"):
            self.current_context = self.agent._perform_context_update(self.current_context, self.model, self.current_messages, "before")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        # Handle context updates after processing
        if self.current_context is not None and self.agent._should_update_context(self.current_context, "after"):
            self.current_context = self.agent._perform_context_update(self.current_context, self.model, self.current_messages, "after")
    
    def __iter__(self) -> Iterator[BaseAgentResponseChunk[T]]:
        """Iterate over agent steps."""
        while not self.is_done and self.current_step < self.max_steps:
            self.current_step += 1
            
            # Format messages with instructions for first step only
            if self.current_step == 1:
                formatted_messages = self._format_messages(
                    messages=self.current_messages,
                    instructions=self.agent.instructions
                )
            else:
                formatted_messages = self.current_messages
            
            # Get language model response
            response = self.model.run(
                messages=formatted_messages,
                tools=[tool.to_dict() for tool in self.agent.tools] if self.agent.tools else None,
                **self.model_kwargs
            )
            
            # Add response to message history
            self.current_messages.append(response.to_message())
            
            # Check if this has tool calls
            if response.has_tool_calls():
                # Execute tools and add their responses to messages
                tool_responses = execute_tools_from_language_model_response(
                    tools=self.agent.tools,
                    response=response
                )
                for tool_resp in tool_responses:
                    self.current_messages.append(tool_resp.to_dict())
                
                # This is not the final step
                self.steps.append(response)
                yield BaseAgentResponseChunk(
                    step_number=self.current_step,
                    response=response,
                    is_final=False
                )
            else:
                # No tool calls - this is the final step
                self.is_done = True
                yield BaseAgentResponseChunk(
                    step_number=self.current_step,
                    response=response,
                    is_final=True
                )
                break
    
    def collect(self) -> BaseAgentResponse[T]:
        """Collect all steps and return final response."""
        final_response = None
        
        for chunk in self:
            if chunk.is_final:
                final_response = chunk.response
                break
        
        if final_response is None:
            # Max steps reached without final response
            if self.steps:
                final_response = self.steps[-1]
            else:
                raise RuntimeError("No response generated")
        
        return _create_agent_response_from_language_model_response(
            response=final_response,
            steps=self.steps,
            context=self.current_context
        )


class BaseAgentAsyncStream(Generic[T]):
    """Async stream of agent responses for async_iter() method."""
    
    def __init__(
        self,
        agent: "BaseAgent[T]",
        messages: LanguageModelMessagesParam,
        model: LanguageModel,
        max_steps: int,
        **kwargs: Any
    ):
        """Initialize the BaseAgentAsyncStream.
        
        Args:
            agent: The agent instance
            messages: The messages to process
            model: The language model to use
            max_steps: Maximum number of steps
            **kwargs: Additional keyword arguments for model.async_run()
        """
        self.agent = agent
        self.messages = messages
        self.model = model
        self.max_steps = max_steps
        self.kwargs = kwargs
        self.current_step = 0
        self.steps: List[LanguageModelResponse[str]] = []
        self.current_messages = self._parse_initial_messages(messages)
        self.is_done = False
    
    def _parse_initial_messages(self, messages: LanguageModelMessagesParam) -> List[Dict[str, Any]]:
        """Parse initial messages into a list of message dicts."""
        return parse_messages_input(messages)
    
    def _format_messages(
        self, 
        messages: List[Dict[str, Any]], 
        instructions: str | None = None
    ) -> List[Dict[str, Any]]:
        """Format messages with instructions."""
        if instructions:
            system_message = {
                "role": "system",
                "content": instructions
            }
            messages = [system_message] + messages
        return consolidate_system_messages(messages)
    
    def __aiter__(self) -> AsyncIterator[BaseAgentResponseChunk[T]]:
        """Async iterate over agent steps."""
        return self
    
    async def __anext__(self) -> BaseAgentResponseChunk[T]:
        """Get the next agent step."""
        if self.is_done or self.current_step >= self.max_steps:
            raise StopAsyncIteration
        
        self.current_step += 1
        
        # Format messages with instructions for first step only
        if self.current_step == 1:
            formatted_messages = self._format_messages(
                messages=self.current_messages,
                instructions=self.agent.instructions
            )
        else:
            formatted_messages = self.current_messages
        
        # Get language model response
        response = await self.model.async_run(
            messages=formatted_messages,
            tools=[tool.to_dict() for tool in self.agent.tools] if self.agent.tools else None,
            **self.kwargs
        )
        
        # Add response to message history
        self.current_messages.append(response.to_message())
        
        # Check if this has tool calls
        if response.has_tool_calls():
            # Execute tools and add their responses to messages
            tool_responses = execute_tools_from_language_model_response(
                tools=self.agent.tools,
                response=response
            )
            for tool_resp in tool_responses:
                self.current_messages.append(tool_resp.to_dict())
            
            # This is not the final step
            self.steps.append(response)
            return BaseAgentResponseChunk(
                step_number=self.current_step,
                response=response,
                is_final=False
            )
        else:
            # No tool calls - this is the final step
            self.is_done = True
            return BaseAgentResponseChunk(
                step_number=self.current_step,
                response=response,
                is_final=True
            )
    
    async def collect(self) -> BaseAgentResponse[T]:
        """Collect all steps and return final response."""
        final_response = None
        
        async for chunk in self:
            if chunk.is_final:
                final_response = chunk.response
                break
        
        if final_response is None:
            # Max steps reached without final response
            if self.steps:
                final_response = self.steps[-1]
            else:
                raise RuntimeError("No response generated")
        
        return _create_agent_response_from_language_model_response(
            response=final_response,
            steps=self.steps,
            context=self.current_context
        )


__all__ = [
    "BaseAgentResponseChunk",
    "BaseAgentStream", 
    "BaseAgentAsyncStream",
]