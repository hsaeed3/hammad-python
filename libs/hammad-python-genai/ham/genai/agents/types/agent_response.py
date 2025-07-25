"""ham.genai.agents.types.agent_response"""

from typing import List, Any, TypeVar, Literal, Generic
from pydantic import Field

try:
    from ham.core.cache import cached
    from ham.core.typing import get_type_description
except ImportError:
    from ...cache import cached  # type: ignore
    from ...typing import get_type_description  # type: ignore
from ...models.language.types import (
    LanguageModelResponse,
)

from .agent_context import AgentContext

__all__ = [
    "AgentResponse",
    "_create_agent_response_from_language_model_response",
]


T = TypeVar("T")


def _create_agent_response_from_language_model_response(
    response: LanguageModelResponse[T],
    steps: List[LanguageModelResponse[str]] | None = None,
    context: Any = None,
) -> "AgentResponse[T]":
    """Create a AgentResponse from a LanguageModelResponse."""
    try:
        return AgentResponse(
            type="agent",
            model=response.model,
            output=response.output,
            content=response.content,
            completion=response.completion,
            refusal=response.refusal,
            steps=steps or [],
            context=context,
        )
    except Exception as e:
        raise ValueError(
            "Failed to create AgentResponse from LanguageModelResponse."
        ) from e


class AgentResponse(LanguageModelResponse[T], Generic[T, AgentContext]):
    """A response generated by an agent, that includes the steps and final
    output during the agent's execution."""

    type: Literal["agent"] = "agent"
    """The type of the response. Always `agent`."""

    steps: List[LanguageModelResponse[str]] = Field(default_factory=list)
    """
    A list of steps taken by the agent **BEFORE** its final output.

    NOTE: If the final output was also the first step, this will be
    empty.
    """

    context: AgentContext | None = None
    """
    The final context object after agent execution.
    
    This is always the final version of the context after any updates
    have been applied during the agent's execution.
    """

    @cached
    def __str__(self) -> str:
        """Pretty prints the response object."""
        output = ">>> AgentResponse:"

        if self.output or self.content:
            output += f"\n{self.output if self.output else self.content}"
        else:
            output += f"\n{self.completion}"

        output += f"\n\n>>> Model: {self.model}"
        # NOTE:
        # added +1 to include final step in the output
        output += f"\n>>> Steps: {len(self.steps) + 1}"
        output += f"\n>>> Output Type: {get_type_description(type(self.output))}"

        # Calculate total tool calls across all steps
        total_tool_calls = 0
        for step in self.steps:
            if step.has_tool_calls():
                total_tool_calls += len(step.tool_calls)

        output += f"\n>>> Total Tool Calls: {total_tool_calls}"

        # Show context if available
        if self.context:
            output += (
                f"\n>>> Final Context: {self._format_context_display(self.context)}"
            )

        return output

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
