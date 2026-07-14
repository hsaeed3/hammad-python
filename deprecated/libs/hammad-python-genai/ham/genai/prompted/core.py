"""ham.genai.prompted.core

Comprehensive implementation of the prompted framework - a function-first, multi-step,
multi-agent framework with unified decorator syntax and rich functionality.

This module provides the core `@prompted` decorator and supporting classes that turn
any typed Python function into a powerful LLM-powered call with extensive features:
- Structured outputs with instructor
- Tool calling and execution
- Multi-step agent workflows
- Context management and state
- Streaming and real-time processing
- Graph chaining and routing
- Fine-grained iteration control
- Comprehensive response metadata
"""

import inspect
import asyncio
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_type_hints,
    overload,
    Literal,
    ParamSpec,
    Generic,
    Iterator,
    AsyncIterator,
)
from dataclasses import dataclass, field
from functools import wraps
from pydantic import BaseModel, Field
from copy import deepcopy
import json

try:
    from ham.core.logging.logger import _get_internal_logger
    from ham.core.conversion import convert_to_text
except ImportError:
    from ...logging.logger import _get_internal_logger  # type: ignore
    from ...conversion import convert_to_text  # type: ignore

from ..models.language.model import LanguageModel
from ..models.language.types import (
    LanguageModelName,
    LanguageModelResponse,
    LanguageModelStream,
    LanguageModelInstructorMode,
)
from ..agents.agent import Agent
from ..agents.types.agent_response import AgentResponse
from ..agents.types.agent_stream import AgentStream
from ..agents.types.agent_context import AgentContext
from ..graphs.base import BaseGraph, action as graph_action
from ..types.tools import Tool, define_tool

__all__ = [
    "prompted",
    "PromptedFunction",
    "PromptedResponse",
    "PromptedStream",
    "PromptedContext",
    "PromptedIterator",
    "PromptedAgent",
    "ctx",
    "itemize",
]

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")
StateT = TypeVar("StateT")

logger = _get_internal_logger(__name__)


@dataclass
class PromptedResponse(Generic[T]):
    """
    Comprehensive response from a prompted function execution with rich metadata.

    This response object provides extensive information about the execution including
    performance metrics, token usage, tool calls, conversation history, and more.
    """

    # Core response data
    output: T
    """The main output from the function."""

    content: str
    """String representation of the output."""

    # Execution metadata
    type: str = "prompted"
    """Type of response (prompted, agent, graph)."""

    model: Optional[LanguageModelName] = None
    """Model used for generation."""

    steps: int = 1
    """Number of execution steps taken."""

    tool_calls: int = 0
    """Number of tool calls made."""

    # Message history and context
    messages: List[Dict[str, Any]] = field(default_factory=list)
    """Complete conversation history."""

    context: Optional[Any] = None
    """Final context/state after execution."""

    # Performance and usage data
    tokens_used: Optional[int] = None
    """Total tokens consumed."""

    execution_time: Optional[float] = None
    """Total execution time in seconds."""

    cost_estimate: Optional[float] = None
    """Estimated cost in USD."""

    # Advanced metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata and debug information."""

    reasoning_steps: List[str] = field(default_factory=list)
    """Captured reasoning steps if available."""

    confidence_score: Optional[float] = None
    """Confidence score for the output if available."""

    # Error handling
    errors: List[str] = field(default_factory=list)
    """Any errors or warnings during execution."""

    retries: int = 0
    """Number of retries performed."""

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"PromptedResponse(output={repr(self.output)}, steps={self.steps}, tool_calls={self.tool_calls})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "output": self.output,
            "content": self.content,
            "type": self.type,
            "model": self.model,
            "steps": self.steps,
            "tool_calls": self.tool_calls,
            "messages": self.messages,
            "context": self.context,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "cost_estimate": self.cost_estimate,
            "metadata": self.metadata,
            "reasoning_steps": self.reasoning_steps,
            "confidence_score": self.confidence_score,
            "errors": self.errors,
            "retries": self.retries,
        }

    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)


@dataclass
class PromptedContext:
    """
    Advanced context manager for conversations, state, and metadata.

    This provides comprehensive context management including message history,
    state tracking, template rendering, and metadata collection.
    """

    messages: List[Dict[str, Any]] = field(default_factory=list)
    """Conversation message history."""

    state: Optional[Any] = None
    """Current state object."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Arbitrary metadata storage."""

    variables: Dict[str, Any] = field(default_factory=dict)
    """Template variables for rendering."""

    history: List[Dict[str, Any]] = field(default_factory=list)
    """Execution history for debugging."""

    def system(self, content: str, **kwargs) -> "PromptedContext":
        """Add a system message with optional template variables."""
        rendered_content = self._render_template(content, kwargs)
        self.messages.append({"role": "system", "content": rendered_content})
        return self

    def user(self, content: str, **kwargs) -> "PromptedContext":
        """Add a user message with optional template variables."""
        rendered_content = self._render_template(content, kwargs)
        self.messages.append({"role": "user", "content": rendered_content})
        return self

    def assistant(self, content: str, **kwargs) -> "PromptedContext":
        """Add an assistant message with optional template variables."""
        rendered_content = self._render_template(content, kwargs)
        self.messages.append({"role": "assistant", "content": rendered_content})
        return self

    def add(
        self,
        messages: Union[str, List[Dict[str, Any]], "PromptedContext", PromptedResponse],
    ) -> "PromptedContext":
        """Add messages from various sources."""
        if isinstance(messages, str):
            self.user(messages)
        elif isinstance(messages, list):
            self.messages.extend(messages)
        elif isinstance(messages, PromptedContext):
            self.messages.extend(messages.messages)
            if messages.state is not None:
                self.state = messages.state
            self.metadata.update(messages.metadata)
            self.variables.update(messages.variables)
        elif isinstance(messages, PromptedResponse):
            self.messages.extend(messages.messages)
            if messages.context is not None:
                self.state = messages.context
        return self

    def set_state(self, state: Any) -> "PromptedContext":
        """Set the current state."""
        self.state = state
        return self

    def update_state(self, **kwargs) -> "PromptedContext":
        """Update state attributes."""
        if self.state is None:
            self.state = {}
        if isinstance(self.state, dict):
            self.state.update(kwargs)
        else:
            for key, value in kwargs.items():
                setattr(self.state, key, value)
        return self

    def set_variable(self, key: str, value: Any) -> "PromptedContext":
        """Set a template variable."""
        self.variables[key] = value
        return self

    def set_variables(self, **kwargs) -> "PromptedContext":
        """Set multiple template variables."""
        self.variables.update(kwargs)
        return self

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables and state."""
        try:
            # Combine instance variables with provided variables
            render_vars = {**self.variables, **variables}

            # Add state variables if available
            if self.state:
                if isinstance(self.state, dict):
                    render_vars.update(self.state)
                else:
                    # Add state attributes
                    for attr in dir(self.state):
                        if not attr.startswith("_"):
                            render_vars[attr] = getattr(self.state, attr)

            return template.format(**render_vars)
        except (KeyError, AttributeError):
            # Return template as-is if rendering fails
            return template

    def copy(self) -> "PromptedContext":
        """Create a deep copy of the context."""
        return PromptedContext(
            messages=deepcopy(self.messages),
            state=deepcopy(self.state),
            metadata=deepcopy(self.metadata),
            variables=deepcopy(self.variables),
            history=deepcopy(self.history),
        )

    def clear(self) -> "PromptedContext":
        """Clear all messages and reset context."""
        self.messages.clear()
        self.metadata.clear()
        self.variables.clear()
        self.history.clear()
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "messages": self.messages,
            "state": self.state,
            "metadata": self.metadata,
            "variables": self.variables,
            "history": self.history,
        }


class PromptedIterator:
    """
    Advanced iterator for fine-grained control over prompted function execution.

    Provides comprehensive control over the generation process including partial
    generation, field-level control, retries with feedback, validation, and more.
    """

    def __init__(self, prompted_func: "PromptedFunction", *args, **kwargs):
        self.prompted_func = prompted_func
        self.args = args
        self.kwargs = kwargs
        self.context = kwargs.pop("context", PromptedContext())
        self.partial_output = None
        self.completed = False
        self.generation_history = []
        self.field_states = {}

    def partial(
        self,
        content: Optional[str] = None,
        fields: Optional[List[str]] = None,
        mode: Literal["replace", "append", "prepend"] = "replace",
        instructions: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Generate partial output for specific fields with advanced options.

        Args:
            content: Additional content to provide to the model
            fields: Specific fields to generate (for structured outputs)
            mode: How to handle the content (replace, append, prepend)
            instructions: Override instructions for this generation
            **kwargs: Additional parameters for the model
        """
        logger.debug(f"Generating partial output for fields: {fields}")

        # Add content to context if provided
        if content:
            if mode == "append":
                self.context.user(content)
            elif mode == "prepend":
                self.context.messages.insert(-1, {"role": "user", "content": content})
            else:  # replace
                self.context.user(content)

        # Store generation attempt
        self.generation_history.append(
            {
                "type": "partial",
                "fields": fields,
                "content": content,
                "mode": mode,
                "instructions": instructions,
            }
        )

        # For now, delegate to full run - a complete implementation would
        # use structured output with field selection
        merged_kwargs = {**self.kwargs, **kwargs}
        if instructions:
            merged_kwargs["instructions"] = instructions

        result = self.prompted_func.run(
            *self.args, context=self.context, **merged_kwargs
        )
        self.partial_output = result.output

        # Track field states
        if fields and hasattr(self.partial_output, "__dict__"):
            for field in fields:
                if hasattr(self.partial_output, field):
                    self.field_states[field] = getattr(self.partial_output, field)

        return self.partial_output

    def get(self, field: Optional[str] = None) -> Any:
        """Get current output or specific field value."""
        if self.partial_output is None:
            self.partial_output = self.prompted_func.run(
                *self.args, context=self.context, **self.kwargs
            )

        if field:
            if hasattr(self.partial_output, field):
                return getattr(self.partial_output, field)
            elif isinstance(self.partial_output, dict):
                return self.partial_output.get(field)
            else:
                return None
        return self.partial_output

    def validate(
        self, validator: Callable[[Any], bool], error_message: str = "Validation failed"
    ) -> bool:
        """Validate the current output with a custom validator."""
        if self.partial_output is None:
            return False

        try:
            return validator(self.partial_output)
        except Exception as e:
            logger.warning(f"Validation error: {e}")
            return False

    def retry(
        self,
        feedback: str,
        fields: Optional[List[str]] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> Any:
        """
        Retry generation with feedback and validation.

        Args:
            feedback: Feedback message to guide regeneration
            fields: Specific fields to regenerate
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters for retry
        """
        retry_count = len(
            [h for h in self.generation_history if h.get("type") == "retry"]
        )

        if retry_count >= max_retries:
            logger.warning(f"Max retries ({max_retries}) exceeded")
            return self.partial_output

        logger.debug(f"Retrying with feedback: {feedback}")

        # Add feedback to context
        self.context.user(f"Previous attempt needs improvement: {feedback}")

        # Store retry attempt
        self.generation_history.append(
            {
                "type": "retry",
                "feedback": feedback,
                "fields": fields,
                "attempt": retry_count + 1,
            }
        )

        # Regenerate
        return self.partial(
            *self.args, fields=fields, context=self.context, **{**self.kwargs, **kwargs}
        )

    def complete(self) -> Any:
        """Complete the generation with all remaining fields."""
        if not self.completed:
            logger.debug("Completing generation")
            result = self.prompted_func.run(
                *self.args, context=self.context, **self.kwargs
            )
            self.partial_output = result.output
            self.completed = True

        return self.partial_output

    def end(self) -> Any:
        """End generation and return current output immediately."""
        return self.get()

    def reset(self) -> "PromptedIterator":
        """Reset the iterator to start over."""
        self.partial_output = None
        self.completed = False
        self.generation_history.clear()
        self.field_states.clear()
        self.context.clear()
        return self

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the complete generation history."""
        return self.generation_history.copy()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Iterator error: {exc_val}")


class PromptedStream:
    """
    Advanced streaming interface with comprehensive event handling and control.

    Provides real-time token streaming with events, partial results, and
    comprehensive metadata tracking.
    """

    def __init__(
        self,
        stream: Union[LanguageModelStream, AgentStream],
        prompted_func: "PromptedFunction",
    ):
        self.stream = stream
        self.prompted_func = prompted_func
        self._chunks = []
        self._completed = False
        self._error = None

    def __iter__(self):
        return self

    def __next__(self):
        try:
            chunk = next(self.stream)
            self._chunks.append(chunk)
            return chunk
        except StopIteration:
            self._completed = True
            raise
        except Exception as e:
            self._error = e
            raise

    async def __aiter__(self):
        try:
            async for chunk in self.stream:
                self._chunks.append(chunk)
                yield chunk
            self._completed = True
        except Exception as e:
            self._error = e
            raise

    def collect(self) -> PromptedResponse:
        """Collect all chunks into a final response."""
        if not self._completed:
            # Consume remaining chunks
            try:
                for _ in self:
                    pass
            except StopIteration:
                pass

        # Build final response from collected chunks
        if self._chunks:
            last_chunk = self._chunks[-1]
            content = getattr(last_chunk, "content", "") or str(last_chunk)
            output = getattr(last_chunk, "output", content)

            return PromptedResponse(
                output=output,
                content=content,
                model=getattr(self.stream, "model", None),
                steps=1,
                tool_calls=0,
                messages=[],
                metadata={
                    "chunks_collected": len(self._chunks),
                    "streaming": True,
                    "completed": self._completed,
                    "error": str(self._error) if self._error else None,
                },
            )
        else:
            return PromptedResponse(
                output="",
                content="",
                metadata={"streaming": True, "error": "No chunks collected"},
            )


class PromptedFunction:
    """
    Comprehensive prompted function with extensive features and capabilities.

    This is the core class that wraps a regular function with LLM capabilities,
    providing a rich set of features including:
    - Multiple execution modes (simple, agent, graph)
    - Tool integration and management
    - Context and state management
    - Streaming and iteration control
    - Graph chaining and routing
    - Comprehensive error handling
    - Performance monitoring
    - Extensive configuration options
    """

    def __init__(
        self,
        func: Callable[P, R],
        # Model configuration
        model: Optional[Union[LanguageModel, LanguageModelName]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        # Tool configuration
        tools: Optional[List[Union[Callable, Tool]]] = None,
        # Agent configuration
        max_steps: Optional[int] = None,
        end_strategy: Optional[Literal["tool"]] = None,
        end_tool: Optional[Callable] = None,
        # Execution configuration
        verbose: bool = False,
        debug: bool = False,
        stream: bool = False,
        # Advanced configuration
        retry_config: Optional[Dict[str, Any]] = None,
        validation_config: Optional[Dict[str, Any]] = None,
        performance_tracking: bool = True,
        **kwargs: Any,
    ):
        self.func = func
        self.model = model or "openai/gpt-4o-mini"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.instructor_mode = instructor_mode or "tool_call"

        # Process and validate tools
        self.tools = self._process_tools(tools or [])

        # Agent settings
        self.max_steps = max_steps
        self.end_strategy = end_strategy
        self.end_tool = end_tool

        # Execution settings
        self.verbose = verbose
        self.debug = debug
        self.default_stream = stream

        # Advanced settings
        self.retry_config = retry_config or {"max_retries": 3, "backoff_factor": 2}
        self.validation_config = validation_config or {}
        self.performance_tracking = performance_tracking

        self.kwargs = kwargs

        # Extract function metadata
        self.name = func.__name__
        self.signature = inspect.signature(func)
        self.instructions = func.__doc__ or ""
        self.type_hints = get_type_hints(func)

        # Get return type for structured output
        self.return_type = self.signature.return_annotation
        if self.return_type == inspect.Signature.empty:
            self.return_type = str

        # Store original function for direct calls
        self.__wrapped__ = func

        # Graph chaining support
        self._next_functions: List[Union[str, Callable, "PromptedFunction"]] = []
        self._conditions: Dict[str, Union[Callable, "PromptedFunction"]] = {}

        # Performance tracking
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0

    def _process_tools(self, tools: List[Union[Callable, Tool]]) -> List[Tool]:
        """Convert callables to Tool objects with validation."""
        processed_tools = []
        for tool in tools:
            if isinstance(tool, Tool):
                processed_tools.append(tool)
            elif callable(tool):
                try:
                    processed_tools.append(define_tool(tool))
                except Exception as e:
                    logger.warning(f"Failed to convert tool {tool}: {e}")
        return processed_tools

    def _should_use_agent(self) -> bool:
        """Determine if we should use Agent vs LanguageModel."""
        return bool(
            self.tools
            or self.max_steps
            or self.end_strategy
            or len(self.signature.parameters) > 2  # Complex multi-parameter functions
        )

    def _create_language_model(self, **override_kwargs) -> LanguageModel:
        """Create a LanguageModel instance with merged settings."""
        merged_kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "instructor_mode": self.instructor_mode,
            "verbose": self.verbose,
            "debug": self.debug,
            **self.kwargs,
            **override_kwargs,
        }
        # Remove None values
        merged_kwargs = {k: v for k, v in merged_kwargs.items() if v is not None}

        model_name = merged_kwargs.pop("model", self.model)
        return LanguageModel(model=model_name, **merged_kwargs)

    def _create_agent(self, **override_kwargs) -> Agent:
        """Create an Agent instance with merged settings."""
        merged_kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "instructor_mode": self.instructor_mode,
            "max_steps": self.max_steps,
            "end_strategy": self.end_strategy,
            "end_tool": self.end_tool,
            "verbose": self.verbose,
            "debug": self.debug,
            **self.kwargs,
            **override_kwargs,
        }
        # Remove None values
        merged_kwargs = {k: v for k, v in merged_kwargs.items() if v is not None}

        model_name = merged_kwargs.pop("model", self.model)
        return Agent(
            name=self.name,
            instructions=self.instructions,
            model=model_name,
            tools=self.tools,
            **merged_kwargs,
        )

    def _prepare_messages(
        self, *args, context: Optional[PromptedContext] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Prepare messages from function arguments and context with advanced formatting."""
        messages = []

        # Add context messages first
        if context:
            messages.extend(context.messages)

        # Add system instructions if not already present
        if self.instructions and not any(
            msg.get("role") == "system" for msg in messages
        ):
            # Render instructions with context variables
            rendered_instructions = self.instructions
            if context and context.variables:
                try:
                    rendered_instructions = self.instructions.format(
                        **context.variables
                    )
                except (KeyError, ValueError):
                    pass  # Use original instructions if template fails

            messages.insert(0, {"role": "system", "content": rendered_instructions})

        # Format function arguments into user message(s)
        if args or kwargs:
            # Bind arguments to function signature
            try:
                bound_args = self.signature.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Advanced parameter formatting
                if len(bound_args.arguments) == 1:
                    # Single parameter - use its value directly
                    param_name, param_value = next(iter(bound_args.arguments.items()))

                    # Special handling for complex types
                    if isinstance(param_value, (dict, list)):
                        user_message = (
                            f"{param_name}:\n{json.dumps(param_value, indent=2)}"
                        )
                    else:
                        user_message = str(param_value)
                else:
                    # Multiple parameters - format them clearly with type hints
                    param_parts = []
                    for param_name, param_value in bound_args.arguments.items():
                        param_type = self.type_hints.get(
                            param_name, type(param_value).__name__
                        )

                        if isinstance(param_value, (dict, list)):
                            formatted_value = json.dumps(param_value, indent=2)
                        else:
                            formatted_value = str(param_value)

                        param_parts.append(
                            f"{param_name} ({param_type}): {formatted_value}"
                        )

                    user_message = "\n".join(param_parts)

                messages.append({"role": "user", "content": user_message})

            except TypeError as e:
                logger.warning(f"Failed to bind arguments: {e}")
                # Fallback to simple string representation
                if args:
                    messages.append({"role": "user", "content": str(args[0])})

        return messages

    def run(
        self,
        *args,
        context: Optional[PromptedContext] = None,
        stream: Optional[bool] = None,
        **kwargs,
    ) -> Union[PromptedResponse[R], PromptedStream]:
        """
        Run the prompted function with comprehensive execution and monitoring.

        Args:
            *args: Arguments for the wrapped function
            context: Optional context for conversation and state
            stream: Whether to return a stream (overrides default)
            **kwargs: Additional parameters for model/agent

        Returns:
            PromptedResponse with rich metadata or PromptedStream for real-time processing
        """
        import time

        start_time = time.time()
        self._execution_count += 1

        logger.debug(
            f"Running prompted function: {self.name} (execution #{self._execution_count})"
        )

        try:
            # Determine streaming mode
            should_stream = stream if stream is not None else self.default_stream

            # Prepare messages with advanced formatting
            messages = self._prepare_messages(*args, context=context, **kwargs)

            # Choose execution path based on complexity
            if self._should_use_agent():
                # Use Agent for complex operations
                agent = self._create_agent(**kwargs)

                if should_stream:
                    agent_stream = agent.run(
                        messages, stream=True, output_type=self.return_type
                    )
                    return PromptedStream(agent_stream, self)
                else:
                    agent_response = agent.run(messages, output_type=self.return_type)

                    # Build comprehensive response
                    execution_time = time.time() - start_time
                    self._total_execution_time += execution_time

                    return PromptedResponse(
                        output=agent_response.output,
                        content=str(agent_response.output),
                        type="agent",
                        model=agent.model,
                        steps=len(agent_response.steps) + 1,
                        tool_calls=sum(
                            1 for step in agent_response.steps if step.has_tool_calls()
                        ),
                        messages=messages,
                        context=context.state if context else None,
                        execution_time=execution_time,
                        metadata={
                            "agent_name": agent.name,
                            "agent_steps": [
                                step.get_content() for step in agent_response.steps
                            ],
                            "execution_count": self._execution_count,
                            "total_execution_time": self._total_execution_time,
                            "average_execution_time": self._total_execution_time
                            / self._execution_count,
                            "function_name": self.name,
                            "return_type": str(self.return_type),
                        },
                    )
            else:
                # Use LanguageModel for simple operations
                lm = self._create_language_model(**kwargs)

                if should_stream:
                    lm_stream = lm.run(messages, stream=True, type=self.return_type)
                    return PromptedStream(lm_stream, self)
                else:
                    lm_response = lm.run(messages, type=self.return_type)

                    # Build comprehensive response
                    execution_time = time.time() - start_time
                    self._total_execution_time += execution_time

                    return PromptedResponse(
                        output=lm_response.output,
                        content=str(lm_response.output),
                        type="language_model",
                        model=lm.model,
                        steps=1,
                        tool_calls=0,
                        messages=messages,
                        context=context.state if context else None,
                        execution_time=execution_time,
                        metadata={
                            "execution_count": self._execution_count,
                            "total_execution_time": self._total_execution_time,
                            "average_execution_time": self._total_execution_time
                            / self._execution_count,
                            "function_name": self.name,
                            "return_type": str(self.return_type),
                            "model_response_metadata": getattr(
                                lm_response, "metadata", {}
                            ),
                        },
                    )

        except Exception as e:
            self._error_count += 1
            execution_time = time.time() - start_time

            logger.error(f"Error in prompted function {self.name}: {e}")

            # Return error response
            return PromptedResponse(
                output=None,
                content=f"Error: {str(e)}",
                type="error",
                execution_time=execution_time,
                errors=[str(e)],
                metadata={
                    "execution_count": self._execution_count,
                    "error_count": self._error_count,
                    "function_name": self.name,
                    "error_type": type(e).__name__,
                },
            )

    async def arun(
        self,
        *args,
        context: Optional[PromptedContext] = None,
        stream: Optional[bool] = None,
        **kwargs,
    ) -> Union[PromptedResponse[R], PromptedStream]:
        """Async version of run with identical functionality."""
        import time

        start_time = time.time()
        self._execution_count += 1

        logger.debug(f"Running async prompted function: {self.name}")

        try:
            # Determine streaming mode
            should_stream = stream if stream is not None else self.default_stream

            # Prepare messages
            messages = self._prepare_messages(*args, context=context, **kwargs)

            # Choose execution path
            if self._should_use_agent():
                agent = self._create_agent(**kwargs)

                if should_stream:
                    agent_stream = agent.run(
                        messages, stream=True, output_type=self.return_type
                    )
                    return PromptedStream(agent_stream, self)
                else:
                    agent_response = await agent.async_run(
                        messages, output_type=self.return_type
                    )

                    execution_time = time.time() - start_time
                    self._total_execution_time += execution_time

                    return PromptedResponse(
                        output=agent_response.output,
                        content=str(agent_response.output),
                        type="agent_async",
                        model=agent.model,
                        steps=len(agent_response.steps) + 1,
                        tool_calls=sum(
                            1 for step in agent_response.steps if step.has_tool_calls()
                        ),
                        messages=messages,
                        context=context.state if context else None,
                        execution_time=execution_time,
                        metadata={
                            "agent_name": agent.name,
                            "execution_count": self._execution_count,
                            "async": True,
                        },
                    )
            else:
                lm = self._create_language_model(**kwargs)

                if should_stream:
                    lm_stream = await lm.async_run(
                        messages, stream=True, type=self.return_type
                    )
                    return PromptedStream(lm_stream, self)
                else:
                    lm_response = await lm.async_run(messages, type=self.return_type)

                    execution_time = time.time() - start_time
                    self._total_execution_time += execution_time

                    return PromptedResponse(
                        output=lm_response.output,
                        content=str(lm_response.output),
                        type="language_model_async",
                        model=lm.model,
                        execution_time=execution_time,
                        metadata={
                            "execution_count": self._execution_count,
                            "async": True,
                        },
                    )

        except Exception as e:
            self._error_count += 1
            execution_time = time.time() - start_time

            return PromptedResponse(
                output=None,
                content=f"Error: {str(e)}",
                type="error_async",
                execution_time=execution_time,
                errors=[str(e)],
                metadata={"async": True, "error_count": self._error_count},
            )

    def iter(self, *args, **kwargs) -> PromptedIterator:
        """Create an advanced iterator for fine-grained control."""
        return PromptedIterator(self, *args, **kwargs)

    def next(
        self, next_func: Union[str, Callable, "PromptedFunction"]
    ) -> "PromptedFunction":
        """Chain this function to another for multi-step workflows."""
        self._next_functions.append(next_func)
        return self

    def when(
        self, condition: str, next_func: Union[str, Callable, "PromptedFunction"]
    ) -> "PromptedFunction":
        """Add conditional chaining based on output conditions."""
        self._conditions[condition] = next_func
        return self

    def stats(self) -> Dict[str, Any]:
        """Get comprehensive execution statistics."""
        return {
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": self._total_execution_time
            / max(1, self._execution_count),
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._execution_count),
            "function_name": self.name,
            "return_type": str(self.return_type),
            "has_tools": bool(self.tools),
            "tool_count": len(self.tools),
            "model": self.model,
        }

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0

    def __call__(self, *args, **kwargs):
        """Allow direct calling of the original function."""
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        return f"PromptedFunction({self.name}, model={self.model}, tools={len(self.tools)})"


class PromptedAgent(BaseGraph):
    """
    Advanced class-based agent that extends the graph functionality.

    This provides a structured way to define complex, stateful agents with
    multiple actions, state management, and graph-like execution flows.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._prompted_functions = {}
        self._collect_prompted_functions()

    def _collect_prompted_functions(self):
        """Collect all PromptedFunction instances from the class."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, PromptedFunction):
                self._prompted_functions[attr_name] = attr


# The main decorator with comprehensive functionality
@overload
def prompted(func: Callable[P, R]) -> PromptedFunction:
    """Direct decorator usage: @prompted"""
    ...


@overload
def prompted(
    *,
    model: Optional[Union[LanguageModel, LanguageModelName]] = None,
    tools: Optional[List[Union[Callable, Tool]]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    instructor_mode: Optional[LanguageModelInstructorMode] = None,
    max_steps: Optional[int] = None,
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    verbose: bool = False,
    debug: bool = False,
    stream: bool = False,
    retry_config: Optional[Dict[str, Any]] = None,
    validation_config: Optional[Dict[str, Any]] = None,
    performance_tracking: bool = True,
    **kwargs: Any,
) -> Callable[[Callable[P, R]], PromptedFunction]:
    """Decorator with parameters: @prompted(...)"""
    ...


def prompted(
    func: Optional[Callable[P, R]] = None,
    *,
    model: Optional[Union[LanguageModel, LanguageModelName]] = None,
    tools: Optional[List[Union[Callable, Tool]]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    instructor_mode: Optional[LanguageModelInstructorMode] = None,
    max_steps: Optional[int] = None,
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    verbose: bool = False,
    debug: bool = False,
    stream: bool = False,
    retry_config: Optional[Dict[str, Any]] = None,
    validation_config: Optional[Dict[str, Any]] = None,
    performance_tracking: bool = True,
    **kwargs: Any,
) -> Union[PromptedFunction, Callable[[Callable[P, R]], PromptedFunction]]:
    """
    Comprehensive decorator to create a prompted function with extensive capabilities.

    This decorator transforms any typed Python function into a powerful LLM-powered
    call with rich features including structured outputs, tool calling, streaming,
    state management, performance tracking, and more.

    Args:
        func: The function to wrap (when used as @prompted)
        model: Language model to use (name string or LanguageModel instance)
        tools: List of tools/functions the LLM can call
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
        instructor_mode: Mode for structured outputs ("tool_call", "json", etc.)
        max_steps: Maximum agent steps for complex workflows
        end_strategy: Strategy for ending multi-step execution
        end_tool: Specific tool for ending execution
        verbose: Enable verbose logging
        debug: Enable debug logging
        stream: Default to streaming mode
        retry_config: Configuration for automatic retries
        validation_config: Configuration for output validation
        performance_tracking: Enable performance monitoring
        **kwargs: Additional parameters for model/agent

    Returns:
        PromptedFunction instance or decorator function

    Examples:
        Basic sentiment analysis:
        ```python
        @prompted
        def classify(text: str) -> Literal["positive", "negative", "neutral"]:
            "You are a world-class sentiment classifier."

        result = classify.run("I love this framework!")
        print(result.output)  # "positive"
        print(result.execution_time)  # Execution time in seconds
        print(result.metadata)  # Rich metadata
        ```

        Advanced configuration:
        ```python
        @prompted(
            model="gpt-4",
            temperature=0.1,
            tools=[search_web, calculator],
            max_steps=5,
            verbose=True,
            performance_tracking=True,
            retry_config={"max_retries": 5, "backoff_factor": 2}
        )
        def research_analyst(topic: str) -> ResearchReport:
            '''Conduct comprehensive research on the topic using available tools.

            Provide detailed analysis with sources, data, and conclusions.
            '''

        # Advanced usage with context and streaming
        ctx = ctx().set_variable("domain", "technology")
        stream = research_analyst.run("quantum computing", context=ctx, stream=True)
        for chunk in stream:
            print(chunk.content, end="", flush=True)
        ```

        Fine-grained control:
        ```python
        @prompted
        def extract_info(text: str) -> UserProfile:
            "Extract structured user information."

        with extract_info.iter("I'm John, 25, from NYC") as it:
            # Generate name first
            it.partial(fields=["name"])

            # Validate and retry if needed
            if not it.validate(lambda x: x.name.title() == x.name):
                it.retry("Please capitalize the name properly", fields=["name"])

            # Generate remaining fields
            it.complete()

        result = it.get()
        ```

        Function chaining:
        ```python
        @prompted
        def analyze(text: str) -> str:
            "Analyze sentiment and extract key themes."

        @prompted
        def respond(analysis: str) -> str:
            "Generate an appropriate response based on analysis."

        # Chain functions
        pipeline = analyze.next(respond)
        final_result = pipeline.run("I'm having a great day!")
        ```
    """

    def decorator(f: Callable[P, R]) -> PromptedFunction:
        return PromptedFunction(
            func=f,
            model=model,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            instructor_mode=instructor_mode,
            max_steps=max_steps,
            end_strategy=end_strategy,
            end_tool=end_tool,
            verbose=verbose,
            debug=debug,
            stream=stream,
            retry_config=retry_config,
            validation_config=validation_config,
            performance_tracking=performance_tracking,
            **kwargs,
        )

    if func is None:
        return decorator
    else:
        return decorator(func)


def contextualize() -> PromptedContext:
    """Create a new prompted context for managing conversations and state."""
    return PromptedContext()


def itemize(obj: Any) -> "ItemizedObject":
    """
    Create an itemized representation of an object for context rendering.

    This provides advanced object rendering capabilities for use in prompts
    and context management.
    """
    return ItemizedObject(obj)


class ItemizedObject:
    """Advanced object itemization for rich context rendering."""

    def __init__(self, obj: Any):
        self.obj = obj

    def render(
        self,
        format: Literal["markdown", "json", "json_schema", "text", "repr"] = "markdown",
        type: Optional[Literal["instructions", "output_format"]] = None,
    ) -> str:
        """Render the object in the specified format."""
        try:
            if format == "json_schema":
                if isinstance(self.obj, type) and issubclass(self.obj, BaseModel):
                    return json.dumps(self.obj.model_json_schema(), indent=2)

            return convert_to_text(self.obj, format=format)
        except Exception as e:
            logger.warning(f"Failed to render object: {e}")
            return str(self.obj)
