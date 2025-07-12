"""hammad.genai.agents.run

Standalone functions for running agents with full parameter typing.
"""

from typing import (
    Any,
    Callable,
    List,
    TypeVar,
    Union,
    Optional,
    Type,
    overload,
    Dict,
    TYPE_CHECKING,
)
from typing_extensions import Literal


if TYPE_CHECKING:
    from ..models.language.model import LanguageModel
    from ..models.language.types import (
        LanguageModelName,
        LanguageModelInstructorMode,
    )
    from .types.agent_response import AgentResponse
    from .types.agent_stream import AgentStream
    from .types.agent_context import AgentContext
    from .types.agent_messages import AgentMessages
    from ..types.tools import Tool
    from httpx import Timeout


from .agent import Agent, AgentSettings


__all__ = [
    "run_agent",
    "async_run_agent",
    "run_agent_iter",
    "async_run_agent_iter",
]

T = TypeVar("T")


# Overloads for run_agent - non-streaming
@overload
def run_agent(
    messages: "AgentMessages",
    *,
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> "AgentResponse[str]": ...


@overload
def run_agent(
    messages: "AgentMessages",
    *,
    output_type: Type[T],
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> "AgentResponse[T]": ...


def run_agent(
    messages: "AgentMessages", verbose: bool = False, debug: bool = False, **kwargs: Any
) -> "AgentResponse[Any]":
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
        verbose: If True, set logger to INFO level for detailed output
        debug: If True, set logger to DEBUG level for maximum verbosity
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
    agent = Agent(verbose=verbose, debug=debug, **kwargs)
    return agent.run(messages, verbose=verbose, debug=debug, **kwargs)


# Overloads for async_run_agent
@overload
async def async_run_agent(
    messages: "AgentMessages",
    *,
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> "AgentResponse[str]": ...


@overload
async def async_run_agent(
    messages: "AgentMessages",
    *,
    output_type: Type[T],
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
) -> "AgentResponse[T]": ...


async def async_run_agent(
    messages: "AgentMessages", verbose: bool = False, debug: bool = False, **kwargs: Any
) -> "AgentResponse[Any]":
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
    agent = Agent(verbose=verbose, debug=debug, **kwargs)
    return await agent.async_run(messages, verbose=verbose, debug=debug, **kwargs)


# Overloads for run_agent_iter
@overload
def run_agent_iter(
    messages: "AgentMessages",
    *,
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
) -> "AgentStream[str]": ...


@overload
def run_agent_iter(
    messages: "AgentMessages",
    *,
    output_type: Type[T],
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
) -> "AgentStream[T]": ...


def run_agent_iter(
    messages: "AgentMessages", verbose: bool = False, debug: bool = False, **kwargs: Any
) -> "AgentStream[Any]":
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
    agent = Agent(verbose=verbose, debug=debug, **kwargs)
    return agent.run(messages, stream=True, verbose=verbose, debug=debug, **kwargs)


# Overloads for async_run_agent_iter
@overload
def async_run_agent_iter(
    messages: "AgentMessages",
    *,
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
) -> "AgentStream[str]": ...


@overload
def async_run_agent_iter(
    messages: "AgentMessages",
    *,
    output_type: Type[T],
    # Agent settings
    name: str = "agent",
    instructions: Optional[str] = None,
    description: Optional[str] = None,
    tools: Union[List["Tool"], Callable, None] = None,
    settings: Optional[AgentSettings] = None,
    # Context management
    context: Optional["AgentContext"] = None,
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
    # Model settings
    model: Optional[Union["LanguageModel", "LanguageModelName"]] = None,
    max_steps: Optional[int] = None,
    instructor_mode: Optional["LanguageModelInstructorMode"] = None,
    # End strategy
    end_strategy: Optional[Literal["tool"]] = None,
    end_tool: Optional[Callable] = None,
    # LM settings
    timeout: Optional[Union[float, str, "Timeout"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    seed: Optional[int] = None,
    user: Optional[str] = None,
) -> "AgentStream[T]": ...


def async_run_agent_iter(
    messages: "AgentMessages", verbose: bool = False, debug: bool = False, **kwargs: Any
) -> "AgentStream[Any]":
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
    agent = Agent(verbose=verbose, debug=debug, **kwargs)
    return agent.run(messages, stream=True, verbose=verbose, debug=debug, **kwargs)
