"""hammad.genai.agents.types.agent_stream"""

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

from ...types.base import BaseGenAIModelStream
from ...types.tools import (
    Tool,
    execute_tools_from_language_model_response,
)
from ...models.language.model import LanguageModel
from ...models.language.types import (
    LanguageModelMessages,
    LanguageModelResponse,
    LanguageModelResponseChunk,
    LanguageModelStream,
    LanguageModelSettings,
)
from ...models.language.utils.requests import (
    parse_messages_input as parse_messages,
    consolidate_system_messages,
)

from .agent_response import (
    AgentResponse,
    _create_agent_response_from_language_model_response,
)
from .agent_context import AgentContext

if TYPE_CHECKING:
    from ..agent import Agent

T = TypeVar("T")


class AgentResponseChunk(LanguageModelResponseChunk[T], Generic[T]):
    """A chunk from an agent response stream representing a single step."""

    def __init__(
        self,
        step_number: int,
        response: LanguageModelResponse[str],
        output: T | None = None,
        content: str | None = None,
        model: str | None = None,
        is_final: bool = False,
        **kwargs: Any,
    ):
        """Initialize a AgentResponseChunk.

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
            output=output if output is not None else response.output,
            content=content if content is not None else response.content,
            model=model if model is not None else response.model,
            is_final=is_final,
            **kwargs,
        )
        self.step_number = step_number
        self.response = response

    def __bool__(self) -> bool:
        """Check if this chunk has meaningful content."""
        return bool(self.response)

    def __str__(self) -> str:
        """String representation of the chunk."""
        output = f"AgentResponseChunk(step={self.step_number}, final={self.is_final})"

        # Show content if available
        if self.output or self.content:
            content_preview = str(self.output if self.output else self.content)
            if len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
            output += f"\nContent: {content_preview}"

        return output


class AgentStream(
    BaseGenAIModelStream[AgentResponseChunk[T]], Generic[T, AgentContext]
):
    """Stream of agent responses that can be used in sync and async contexts."""

    def __init__(
        self,
        agent: "Agent[T]",
        messages: LanguageModelMessages,
        model: Optional[Union[LanguageModel, str]] = None,
        max_steps: Optional[int] = None,
        context: Optional[AgentContext] = None,
        output_type: Optional[Type[T]] = None,
        stream: bool = False,
        **kwargs: Any,
    ):
        self.agent = agent
        self.messages = messages
        self.context = context
        self.output_type = output_type
        self.stream = stream
        self.kwargs = kwargs
        self.current_step = 0
        self.steps: List[LanguageModelResponse[str]] = []
        self.current_messages = parse_messages(messages)
        self.is_done = False
        self._final_response: Optional[LanguageModelResponse[str]] = None

        # Model setup
        if model is None:
            self.model = agent.model
        elif isinstance(model, str):
            self.model = LanguageModel(model=model)
        else:
            self.model = model

        # Max steps setup
        self.max_steps = max_steps or agent.settings.max_steps

        # Context handling
        self.current_context = context
        self.initial_context = context

        # Model kwargs setup
        self.model_kwargs = kwargs.copy()
        if output_type:
            self.model_kwargs["type"] = output_type
        if agent.instructor_mode:
            self.model_kwargs["instructor_mode"] = agent.instructor_mode
        if stream:
            self.model_kwargs["stream"] = stream

    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.agent.instructions:
            system_content = self.agent.instructions

            # Add context if available
            if self.current_context is not None:
                from ..agent import _format_context_for_instructions

                context_str = _format_context_for_instructions(
                    self.current_context, self.agent.context_format
                )
                if context_str:
                    system_content += f"\n\nContext:\n{context_str}"

            system_message = {"role": "system", "content": system_content}
            messages = [system_message] + messages
        return consolidate_system_messages(messages)

    def _process_response(
        self, response: LanguageModelResponse
    ) -> AgentResponseChunk[T]:
        self.current_messages.append(response.to_message())

        if response.has_tool_calls:
            tool_responses = execute_tools_from_language_model_response(
                tools=self.agent.tools, response=response
            )
            for tool_resp in tool_responses:
                self.current_messages.append(tool_resp.to_dict())

            self.steps.append(response)
            return AgentResponseChunk(
                step_number=self.current_step, response=response, is_final=False
            )
        else:
            self.is_done = True
            self._final_response = response

            # Update context after processing if configured
            if self.current_context and self.agent._should_update_context(
                self.current_context, "after"
            ):
                self.current_context = self.agent._perform_context_update(
                    context=self.current_context,
                    model=self.model,
                    current_messages=self.current_messages,
                    timing="after",
                )

            return AgentResponseChunk(
                step_number=self.current_step, response=response, is_final=True
            )

    def __iter__(self) -> Iterator[AgentResponseChunk[T]]:
        # The context manager handling should be managed by the agent's run method
        while not self.is_done and self.current_step < self.max_steps:
            self.current_step += 1

            # Update context before processing if configured
            if self.current_context and self.agent._should_update_context(
                self.current_context, "before"
            ):
                self.current_context = self.agent._perform_context_update(
                    context=self.current_context,
                    model=self.model,
                    current_messages=self.current_messages,
                    timing="before",
                )

            formatted_messages = self.current_messages
            if self.current_step == 1:
                formatted_messages = self._format_messages(self.current_messages)

            response = self.model.run(
                messages=formatted_messages,
                tools=[tool.model_dump() for tool in self.agent.tools]
                if self.agent.tools
                else None,
                **self.model_kwargs,
            )

            chunk = self._process_response(response)
            yield chunk
            if chunk.is_final:
                break

    def __aiter__(self) -> AsyncIterator[AgentResponseChunk[T]]:
        return self

    async def __anext__(self) -> AgentResponseChunk[T]:
        if self.is_done or self.current_step >= self.max_steps:
            raise StopAsyncIteration

        # The context manager handling should be managed by the agent's run method
        self.current_step += 1

        # Update context before processing if configured
        if self.current_context and self.agent._should_update_context(
            self.current_context, "before"
        ):
            self.current_context = self.agent._perform_context_update(
                context=self.current_context,
                model=self.model,
                current_messages=self.current_messages,
                timing="before",
            )

        formatted_messages = self.current_messages
        if self.current_step == 1:
            formatted_messages = self._format_messages(self.current_messages)

        response = await self.model.async_run(
            messages=formatted_messages,
            tools=[tool.model_dump() for tool in self.agent.tools]
            if self.agent.tools
            else None,
            **self.model_kwargs,
        )

        chunk = self._process_response(response)
        if chunk.is_final:
            self.is_done = True
        return chunk

    def _build_response(self) -> AgentResponse[T, AgentContext]:
        if self._final_response:
            final_response = self._final_response
        elif self.steps:
            final_response = self.steps[-1]
        else:
            raise RuntimeError("No response generated by the agent.")

        return _create_agent_response_from_language_model_response(
            response=final_response,
            steps=self.steps,
            context=self.current_context,
        )

    def _format_context_display(self, context: AgentContext) -> str:
        """Format context for display in string representation."""
        if context is None:
            return "None"

        try:
            # For Pydantic models, show as dict
            if hasattr(context, "model_dump"):
                context_dict = context.model_dump()
            elif isinstance(context, dict):
                context_dict = context
            else:
                return str(context)

            # Format as compact JSON-like string
            items = []
            for key, value in context_dict.items():
                if isinstance(value, str):
                    items.append(f"{key}='{value}'")
                else:
                    items.append(f"{key}={value}")

            return "{" + ", ".join(items) + "}"
        except Exception:
            return str(context)

    def collect(self) -> AgentResponse[T, AgentContext]:
        """Collect all steps and return final response."""
        for _ in self:
            pass
        return self._build_response()

    async def async_collect(self) -> AgentResponse[T, AgentContext]:
        """Collect all steps and return final response."""
        async for _ in self:
            pass
        return self._build_response()
