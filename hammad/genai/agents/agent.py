"""hammad.genai.agents.agent"""

from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    List,
    Type,
    TypeVar,
    Optional,
    Union,
    Dict,
    overload,
    TYPE_CHECKING,
)
from pydantic import BaseModel, Field, create_model
from dataclasses import dataclass, field
from enum import Enum
import json

from ..types.base import BaseGenAIModel, BaseGenAIModelSettings
from ..models.language.model import LanguageModel
from ..models.language.types import (
    LanguageModelResponse,
    LanguageModelName,
    LanguageModelInstructorMode,
)
from ..types.tools import (
    Tool,
    define_tool,
    execute_tools_from_language_model_response,
)
from ..models.language.utils.requests import (
    parse_messages_input as parse_messages,
    consolidate_system_messages,
)
from ...formatting.text.converters import convert_to_text
from .types.agent_response import (
    AgentResponse,
    _create_agent_response_from_language_model_response,
)
from .types.agent_stream import AgentStream
from .types.agent_context import AgentContext
from .types.agent_event import AgentEvent
from .types.agent_hooks import HookManager, HookDecorator
from .types.agent_messages import AgentMessages

if TYPE_CHECKING:
    pass


T = TypeVar("T")


@dataclass
class AgentSettings:
    """Settings object that controls the default behavior of an agent's run."""

    max_steps: int = field(default=10)
    """The maximum amount of steps the agent can take before stopping."""

    add_name_to_instructions: bool = field(default=True)
    """Whether to add the agent name to the instructions."""

    context_format: Literal["json", "python", "markdown"] = field(default="json")
    """Format for context in instructions."""

    # Context management settings
    context_updates: Optional[
        Union[List[Literal["before", "after"]], Literal["before", "after"]]
    ] = field(default=None)
    """When to update context ('before', 'after', or both)."""

    context_confirm: bool = field(default=False)
    """Whether to confirm context updates."""

    context_strategy: Literal["selective", "all"] = field(default="all")
    """Strategy for context updates."""

    context_max_retries: int = field(default=3)
    """Maximum retries for context updates."""

    context_confirm_instructions: Optional[str] = field(default=None)
    """Custom instructions for context confirmation."""

    context_selection_instructions: Optional[str] = field(default=None)
    """Custom instructions for context selection."""

    context_update_instructions: Optional[str] = field(default=None)
    """Custom instructions for context updates."""


class AgentModelSettings(BaseGenAIModelSettings):
    """Agent-specific model settings that extend the base model settings."""

    instructor_mode: Optional[LanguageModelInstructorMode] = None
    """Instructor mode for structured outputs."""

    max_steps: int = 10
    """Maximum number of steps the agent can take."""

    add_name_to_instructions: bool = True
    """Whether to add the agent name to the instructions."""

    context_format: Literal["json", "python", "markdown"] = "json"
    """Format for context in instructions."""

    # Context management settings
    context_updates: Optional[
        Union[List[Literal["before", "after"]], Literal["before", "after"]]
    ] = None
    """When to update context ('before', 'after', or both)."""

    context_confirm: bool = False
    """Whether to confirm context updates."""

    context_strategy: Literal["selective", "all"] = "all"
    """Strategy for context updates."""

    context_max_retries: int = 3
    """Maximum retries for context updates."""

    context_confirm_instructions: Optional[str] = None
    """Custom instructions for context confirmation."""

    context_selection_instructions: Optional[str] = None
    """Custom instructions for context selection."""

    context_update_instructions: Optional[str] = None
    """Custom instructions for context updates."""


def _build_tools(tools: List[Tool] | Callable | None) -> List[Tool]:
    """Builds a list of tools from a list of tools or a callable that returns a list of tools."""
    if tools is None:
        return []
    if callable(tools):
        return [define_tool(tools)]

    processed_tools = []
    for tool in tools:
        if not isinstance(tool, Tool):
            tool = define_tool(tool)
        processed_tools.append(tool)

    return processed_tools


def _get_instructions(
    name: str,
    instructions: Optional[str],
    add_name_to_instructions: bool,
) -> Optional[str]:
    """Gets the instructions for an agent."""
    if add_name_to_instructions and name:
        base_instructions = instructions or ""
        return f"You are {name}.\n\n{base_instructions}".strip()
    return instructions


def _format_context_for_instructions(
    context: AgentContext | None,
    context_format: Literal["json", "python", "markdown"] = "json",
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
    context: AgentContext, updates: Dict[str, Any]
) -> AgentContext:
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


class Agent(BaseGenAIModel, Generic[T]):
    """A generative AI agent that can execute tools, generate structured outputs,
    and maintain context across multiple conversation steps.
    """

    model: LanguageModelName = "openai/gpt-4o-mini"
    """The language model to use for the agent."""

    name: str = "agent"
    """The name of the agent."""

    description: Optional[str] = None
    """A description of the agent."""

    instructions: Optional[str] = None
    """System instructions for the agent."""

    tools: List[Tool] = Field(default_factory=list)
    """List of tools available to the agent."""

    settings: AgentSettings = Field(default_factory=AgentSettings)
    """Agent-specific settings."""

    instructor_mode: Optional[LanguageModelInstructorMode] = None
    """Instructor mode for structured outputs."""

    def __init__(
        self,
        name: str = "agent",
        instructions: Optional[str] = None,
        model: Union[LanguageModel, LanguageModelName] = "openai/gpt-4o-mini",
        description: Optional[str] = None,
        tools: Union[List[Tool], Callable, None] = None,
        settings: Optional[AgentSettings] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        # Context management parameters
        context_updates: Optional[
            Union[List[Literal["before", "after"]], Literal["before", "after"]]
        ] = None,
        context_confirm: bool = False,
        context_strategy: Literal["selective", "all"] = "all",
        context_max_retries: int = 3,
        context_confirm_instructions: Optional[str] = None,
        context_selection_instructions: Optional[str] = None,
        context_update_instructions: Optional[str] = None,
        context_format: Literal["json", "python", "markdown"] = "json",
        **kwargs: Any,
    ):
        # Initialize BaseGenAIModel with basic parameters
        super().__init__(
            model=model if isinstance(model, str) else model.model, **kwargs
        )

        # Agent-specific initialization
        self.name = name
        self.description = description
        self.tools = _build_tools(tools)
        self.settings = settings or AgentSettings()
        self.instructor_mode = instructor_mode

        # Process instructions
        self.instructions = _get_instructions(
            name=name,
            instructions=instructions,
            add_name_to_instructions=self.settings.add_name_to_instructions,
        )

        # Initialize the language model
        if isinstance(model, LanguageModel):
            self._language_model = model
        else:
            self._language_model = LanguageModel(model=model, **kwargs)

        # Context management settings
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

    @property
    def language_model(self) -> LanguageModel:
        """Get the underlying language model."""
        return self._language_model

    def _should_update_context(
        self, context: AgentContext, timing: Literal["before", "after"]
    ) -> bool:
        """Determine if context should be updated based on timing and configuration."""
        if not self.context_updates:
            return False

        if isinstance(self.context_updates, str):
            return self.context_updates == timing
        else:
            return timing in self.context_updates

    def _create_context_confirm_model(self):
        """Create IsUpdateRequired model for context confirmation."""
        return create_model("IsUpdateRequired", decision=(bool, ...))

    def _create_context_selection_model(self, context: AgentContext):
        """Create FieldsToUpdate model for selective context updates."""
        if isinstance(context, BaseModel):
            field_names = list(context.model_fields.keys())
        elif isinstance(context, dict):
            field_names = list(context.keys())
        else:
            raise ValueError(
                f"Cannot create selection model for context type {type(context)}"
            )

        FieldEnum = Enum("FieldEnum", {name: name for name in field_names})
        return create_model("FieldsToUpdate", fields=(List[FieldEnum], ...))

    def _create_context_update_model(
        self, context: AgentContext, field_name: str = None
    ):
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
                field_name.capitalize(), **{field_name: (field_type, ...)}
            )
        else:
            # All fields update
            return create_model("Update", updates=(Dict[str, Any], ...))

    def _perform_context_update(
        self,
        context: AgentContext,
        model: LanguageModel,
        current_messages: List[Dict[str, Any]],
        timing: Literal["before", "after"],
    ) -> AgentContext:
        """Perform context update with retries and error handling."""
        updated_context = context

        for attempt in range(self.context_max_retries):
            try:
                # Check if update is needed (if confirmation is enabled)
                if self.context_confirm:
                    confirm_model = self._create_context_confirm_model()
                    confirm_instructions = f"Based on the conversation, determine if the context should be updated {timing} processing."
                    if self.context_confirm_instructions:
                        confirm_instructions += (
                            f"\n\n{self.context_confirm_instructions}"
                        )

                    confirm_response = model.run(
                        messages=current_messages
                        + [{"role": "user", "content": confirm_instructions}],
                        type=confirm_model,
                        instructor_mode=self.instructor_mode,
                    )

                    if not confirm_response.output.decision:
                        return updated_context

                # Perform the update based on strategy
                if self.context_strategy == "selective":
                    # Get fields to update
                    selection_model = self._create_context_selection_model(
                        updated_context
                    )
                    selection_instructions = f"Select which fields in the context should be updated {timing} processing."
                    if self.context_selection_instructions:
                        selection_instructions += (
                            f"\n\n{self.context_selection_instructions}"
                        )

                    selection_response = model.run(
                        messages=current_messages
                        + [{"role": "user", "content": selection_instructions}],
                        type=selection_model,
                        instructor_mode=self.instructor_mode,
                    )

                    # Update each selected field
                    for field_enum in selection_response.output.fields:
                        field_name = field_enum.value
                        field_model = self._create_context_update_model(
                            updated_context, field_name
                        )
                        field_instructions = (
                            f"Update the {field_name} field in the context."
                        )
                        if self.context_update_instructions:
                            field_instructions += (
                                f"\n\n{self.context_update_instructions}"
                            )

                        field_response = model.run(
                            messages=current_messages
                            + [{"role": "user", "content": field_instructions}],
                            type=field_model,
                            instructor_mode=self.instructor_mode,
                        )

                        # Apply the update
                        field_updates = {
                            field_name: getattr(field_response.output, field_name)
                        }
                        updated_context = _update_context_object(
                            updated_context, field_updates
                        )

                else:  # strategy == "all"
                    # Update all fields at once
                    update_model = self._create_context_update_model(updated_context)
                    update_instructions = f"Update the context {timing} processing."
                    if self.context_update_instructions:
                        update_instructions += f"\n\n{self.context_update_instructions}"

                    update_response = model.run(
                        messages=current_messages
                        + [{"role": "user", "content": update_instructions}],
                        type=update_model,
                        instructor_mode=self.instructor_mode,
                    )

                    # Apply the updates
                    updated_context = _update_context_object(
                        updated_context, update_response.output.updates
                    )

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

    def _format_messages_with_context(
        self, messages: List[Dict[str, Any]], context: Optional[AgentContext] = None
    ) -> List[Dict[str, Any]]:
        """Format messages with instructions and context."""
        formatted_messages = messages.copy()

        if self.instructions:
            system_content = self.instructions

            # Add context if provided
            if context is not None:
                context_str = _format_context_for_instructions(
                    context, self.context_format
                )
                if context_str:
                    system_content += f"\n\nContext:\n{context_str}"

            system_message = {"role": "system", "content": system_content}
            formatted_messages = [system_message] + formatted_messages

        return consolidate_system_messages(formatted_messages)

    # Overloaded run methods for streaming support
    @overload
    def run(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        *,
        stream: Literal[False] = False,
        **kwargs: Any,
    ) -> AgentResponse[T]: ...

    @overload
    def run(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        *,
        stream: Literal[True],
        **kwargs: Any,
    ) -> AgentStream[T]: ...

    def run(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[AgentResponse[T], AgentStream[T]]:
        """Runs this agent and returns a final agent response or stream.

        You can override defaults assigned to this agent from this function directly.

        Args:
            messages: The messages to process. Can be:
                - A single string: "What's the weather like?"
                - A list of message dicts: [{"role": "user", "content": "Hello"}]
                - A list of strings: ["Hello", "How are you?"]
            model: The model to use for this run (overrides default).
                - Can be a LanguageModel instance or model name string like "gpt-4"
            max_steps: Maximum number of steps to execute (overrides default).
                - Useful for limiting tool usage or preventing infinite loops
            context: Context object for the agent (overrides default).
                - Any object that provides additional context for the conversation
            output_type: The expected output type (overrides default).
                - Use for structured outputs: output_type=MyPydanticModel
                - Defaults to str for unstructured text responses
            stream: Whether to return a stream instead of a final response.
                - If True, returns AgentStream for real-time processing
                - If False, returns complete AgentResponse
            **kwargs: Additional keyword arguments passed to the language model.
                - Examples: temperature=0.7, top_p=0.9, presence_penalty=0.1

        Returns:
            AgentResponse or AgentStream depending on stream parameter.
            - AgentResponse: Contains final output, steps taken, and metadata
            - AgentStream: Iterator yielding intermediate steps and final result

        Examples:
            Basic text conversation:
            >>> agent = Agent()
            >>> response = agent.run("Hello, how are you?")
            >>> print(response.output)
            "Hello! I'm doing well, thank you for asking."

            With custom model and parameters:
            >>> response = agent.run(
            ...     messages="Explain quantum computing",
            ...     model="gpt-4",
            ...     max_steps=5,
            ...     temperature=0.3
            ... )

            Structured output with Pydantic model:
            >>> from pydantic import BaseModel
            >>> class Summary(BaseModel):
            ...     title: str
            ...     key_points: List[str]
            >>> response = agent.run(
            ...     "Summarize the benefits of renewable energy",
            ...     output_type=Summary
            ... )
            >>> print(response.output.title)
            >>> print(response.output.key_points)

            Streaming for real-time results:
            >>> stream = agent.run(
            ...     "Write a long story about space exploration",
            ...     stream=True
            ... )
            >>> for chunk in stream:
            ...     print(chunk.output, end="", flush=True)

            With context for additional information:
            >>> context = {"user_preferences": "technical explanations"}
            >>> response = agent.run(
            ...     "How does machine learning work?",
            ...     context=context
            ... )
        """
        # Handle streaming
        if stream:
            return AgentStream(
                agent=self,
                messages=messages,
                model=model,
                max_steps=max_steps,
                context=context,
                output_type=output_type,
                stream=stream,
                **kwargs,
            )

        # Use provided model or default
        if model is None:
            working_model = self.language_model
        elif isinstance(model, str):
            working_model = LanguageModel(model=model)
        else:
            working_model = model

        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.settings.max_steps

        # Parse initial messages
        parsed_messages = parse_messages(messages)
        current_messages = parsed_messages.copy()
        steps: List[LanguageModelResponse[str]] = []

        # RUN MAIN AGENTIC LOOP
        for step in range(max_steps):
            # Format messages with instructions and context for first step only
            if step == 0:
                formatted_messages = self._format_messages_with_context(
                    messages=current_messages,
                    context=context,
                )
            else:
                formatted_messages = current_messages

            # Prepare kwargs for language model
            model_kwargs = kwargs.copy()
            if output_type:
                model_kwargs["type"] = output_type
            if self.instructor_mode:
                model_kwargs["instructor_mode"] = self.instructor_mode

            # Get language model response
            response = working_model.run(
                messages=formatted_messages,
                tools=[tool.model_dump() for tool in self.tools]
                if self.tools
                else None,
                **model_kwargs,
            )

            # Check if response has tool calls
            if response.has_tool_calls():
                # Add response to message history (with tool calls)
                current_messages.append(response.to_message())

                # Execute tools and add their responses to messages
                tool_responses = execute_tools_from_language_model_response(
                    tools=self.tools, response=response
                )
                # Add tool responses to message history
                for tool_resp in tool_responses:
                    current_messages.append(tool_resp.to_dict())

                # This is not the final step, add to steps
                steps.append(response)
            else:
                # No tool calls - this is the final step
                return _create_agent_response_from_language_model_response(
                    response=response, steps=steps, context=context
                )

        # Max steps reached - return last response
        if steps:
            final_response = steps[-1]
        else:
            # No steps taken, make a final call
            final_response = working_model.run(
                messages=self._format_messages_with_context(
                    messages=current_messages,
                    context=context,
                ),
                **model_kwargs,
            )

        return _create_agent_response_from_language_model_response(
            response=final_response, steps=steps, context=context
        )

    async def async_run(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        **kwargs: Any,
    ) -> AgentResponse[T]:
        """Runs this agent asynchronously and returns a final agent response.

        You can override defaults assigned to this agent from this function directly.
        This is the async version of run() for non-blocking execution.

        Args:
            messages: The messages to process. Can be:
                - A single string: "What's the weather like?"
                - A list of message dicts: [{"role": "user", "content": "Hello"}]
                - A list of strings: ["Hello", "How are you?"]
            model: The model to use for this run (overrides default).
                - Can be a LanguageModel instance or model name string like "gpt-4"
            max_steps: Maximum number of steps to execute (overrides default).
                - Useful for limiting tool usage or preventing infinite loops
            context: Context object for the agent (overrides default).
                - Any object that provides additional context for the conversation
            output_type: The expected output type (overrides default).
                - Use for structured outputs: output_type=MyPydanticModel
                - Defaults to str for unstructured text responses
            **kwargs: Additional keyword arguments passed to the language model.
                - Examples: temperature=0.7, top_p=0.9, presence_penalty=0.1

        Returns:
            AgentResponse containing the final output, steps taken, and metadata.

        Examples:
            Basic async usage:
            >>> import asyncio
            >>> agent = Agent()
            >>> async def main():
            ...     response = await agent.async_run("Hello, how are you?")
            ...     print(response.output)
            >>> asyncio.run(main())

            Multiple concurrent requests:
            >>> async def process_multiple():
            ...     tasks = [
            ...         agent.async_run("What's 2+2?"),
            ...         agent.async_run("What's the capital of France?"),
            ...         agent.async_run("Explain photosynthesis")
            ...     ]
            ...     responses = await asyncio.gather(*tasks)
            ...     return responses

            With structured output:
            >>> from pydantic import BaseModel
            >>> class Analysis(BaseModel):
            ...     sentiment: str
            ...     confidence: float
            >>> async def analyze_text():
            ...     response = await agent.async_run(
            ...         "Analyze the sentiment of: 'I love this product!'",
            ...         output_type=Analysis
            ...     )
            ...     return response.output

            With custom model and context:
            >>> async def custom_run():
            ...     context = {"domain": "medical", "expertise_level": "expert"}
            ...     response = await agent.async_run(
            ...         "Explain diabetes",
            ...         model="gpt-4",
            ...         context=context,
            ...         temperature=0.2
            ...     )
            ...     return response.output
        """
        # Use provided model or default
        if model is None:
            working_model = self.language_model
        elif isinstance(model, str):
            working_model = LanguageModel(model=model)
        else:
            working_model = model

        # Use provided max_steps or default
        if max_steps is None:
            max_steps = self.settings.max_steps

        # Parse initial messages
        parsed_messages = parse_messages(messages)
        current_messages = parsed_messages.copy()
        steps: List[LanguageModelResponse[str]] = []

        # RUN MAIN AGENTIC LOOP
        for step in range(max_steps):
            # Format messages with instructions and context for first step only
            if step == 0:
                formatted_messages = self._format_messages_with_context(
                    messages=current_messages,
                    context=context,
                )
            else:
                formatted_messages = current_messages

            # Prepare kwargs for language model
            model_kwargs = kwargs.copy()
            if output_type:
                model_kwargs["type"] = output_type
            if self.instructor_mode:
                model_kwargs["instructor_mode"] = self.instructor_mode

            # Get language model response
            response = await working_model.async_run(
                messages=formatted_messages,
                tools=[tool.model_dump() for tool in self.tools]
                if self.tools
                else None,
                **model_kwargs,
            )

            # Check if response has tool calls
            if response.has_tool_calls():
                # Add response to message history (with tool calls)
                current_messages.append(response.to_message())

                # Execute tools and add their responses to messages
                tool_responses = execute_tools_from_language_model_response(
                    tools=self.tools, response=response
                )
                # Add tool responses to message history
                for tool_resp in tool_responses:
                    current_messages.append(tool_resp.to_dict())

                # This is not the final step, add to steps
                steps.append(response)
            else:
                # No tool calls - this is the final step
                return _create_agent_response_from_language_model_response(
                    response=response, steps=steps, context=context
                )

        # Max steps reached - return last response
        if steps:
            final_response = steps[-1]
        else:
            # No steps taken, make a final call
            final_response = await working_model.async_run(
                messages=self._format_messages_with_context(
                    messages=current_messages,
                    context=context,
                ),
                **model_kwargs,
            )

        return _create_agent_response_from_language_model_response(
            response=final_response, steps=steps, context=context
        )

    def stream(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        **kwargs: Any,
    ) -> AgentStream[T]:
        """Create a stream that yields agent steps.

        Args:
            messages: The input messages to process
            model: Language model to use (overrides agent's default)
            max_steps: Maximum number of steps to take
            context: Context object to maintain state
            output_type: Type for structured output
            **kwargs: Additional parameters for the language model

        Returns:
            An AgentStream that can be iterated over
        """
        return AgentStream(
            agent=self,
            messages=messages,
            model=model,
            max_steps=max_steps,
            context=context,
            output_type=output_type,
            stream=True,
            **kwargs,
        )

    def iter(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        **kwargs: Any,
    ) -> AgentStream[T]:
        """Iterate over agent steps, yielding each step response.

        You can override defaults assigned to this agent from this function directly.
        Returns an AgentStream that yields intermediate steps and the final result.

        Args:
            messages: The messages to process. Can be:
                - A single string: "What's the weather like?"
                - A list of message dicts: [{"role": "user", "content": "Hello"}]
                - A list of strings: ["Hello", "How are you?"]
            model: The model to use for this run (overrides default).
                - Can be a LanguageModel instance or model name string like "gpt-4"
            max_steps: Maximum number of steps to execute (overrides default).
                - Useful for limiting tool usage or preventing infinite loops
            context: Context object for the agent (overrides default).
                - Any object that provides additional context for the conversation
            output_type: The expected output type (overrides default).
                - Use for structured outputs: output_type=MyPydanticModel
                - Defaults to str for unstructured text responses
            **kwargs: Additional keyword arguments passed to the language model.
                - Examples: temperature=0.7, top_p=0.9, presence_penalty=0.1

        Returns:
            AgentStream that can be iterated over to get each step response,
            including tool calls and intermediate reasoning steps.

        Examples:
            Basic iteration over steps:
            >>> agent = Agent(tools=[calculator_tool])
            >>> stream = agent.iter("What's 25 * 47?")
            >>> for step in stream:
            ...     print(f"Step {step.step_number}: {step.output}")
            ...     if step.tool_calls:
            ...         print(f"Tool calls: {len(step.tool_calls)}")

            Real-time processing with streaming:
            >>> stream = agent.iter("Write a poem about nature")
            >>> for chunk in stream:
            ...     if chunk.output:
            ...         print(chunk.output, end="", flush=True)
            ...     if chunk.is_final:
            ...         print("\n--- Final response ---")

            With structured output iteration:
            >>> from pydantic import BaseModel
            >>> class StepAnalysis(BaseModel):
            ...     reasoning: str
            ...     confidence: float
            >>> stream = agent.iter(
            ...     "Analyze this step by step: Why is the sky blue?",
            ...     output_type=StepAnalysis
            ... )
            >>> for step in stream:
            ...     if step.output:
            ...         print(f"Reasoning: {step.output.reasoning}")
            ...         print(f"Confidence: {step.output.confidence}")

            Processing with custom model and context:
            >>> context = {"domain": "science", "depth": "detailed"}
            >>> stream = agent.iter(
            ...     "Explain quantum entanglement",
            ...     model="gpt-4",
            ...     context=context,
            ...     max_steps=3,
            ...     temperature=0.1
            ... )
            >>> results = []
            >>> for step in stream:
            ...     results.append(step.output)
            ...     if step.is_final:
            ...         break

            Error handling during iteration:
            >>> try:
            ...     stream = agent.iter("Complex calculation task")
            ...     for step in stream:
            ...         if step.error:
            ...             print(f"Error in step: {step.error}")
            ...         else:
            ...             print(f"Step result: {step.output}")
            ... except Exception as e:
            ...     print(f"Stream error: {e}")
        """
        return AgentStream(
            agent=self,
            messages=messages,
            model=model,
            max_steps=max_steps,
            context=context,
            output_type=output_type,
            stream=True,
            **kwargs,
        )

    def async_iter(
        self,
        messages: AgentMessages,
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        **kwargs: Any,
    ) -> AgentStream[T]:
        """Async iterate over agent steps, yielding each step response.

        Args:
            messages: The input messages to process
            model: Language model to use (overrides agent's default)
            max_steps: Maximum number of steps to take
            context: Context object to maintain state
            output_type: Type for structured output
            **kwargs: Additional parameters for the language model

        Returns:
            An AgentStream that can be iterated over asynchronously
        """
        return AgentStream(
            agent=self,
            messages=messages,
            model=model,
            max_steps=max_steps,
            context=context,
            output_type=output_type,
            stream=True,
            **kwargs,
        )


__all__ = [
    "Agent",
    "AgentSettings",
    "AgentModelSettings",
    "AgentEvent",
    "HookManager",
    "HookDecorator",
]
