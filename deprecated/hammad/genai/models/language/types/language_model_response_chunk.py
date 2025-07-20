"""hammad.genai.language_models.language_model_response_chunk"""

from typing import TypeVar, Optional, Any, Literal

from ....types.base import BaseGenAIModelEvent

__all__ = [
    "LanguageModelResponseChunk",
]


T = TypeVar("T")


class LanguageModelResponseChunk(BaseGenAIModelEvent[T]):
    """Represents a chunk of data from a language model response stream.

    This class unifies chunks from both LiteLLM and Instructor streaming,
    providing a consistent interface for processing streaming responses.
    """

    type: Literal["language_model"] = "language_model"
    """The type of the event, always `language_model`."""

    content: Optional[str] = None
    """The content delta for this chunk."""

    output: Optional[T] = None
    """The structured output for this chunk (from instructor)."""

    model: Optional[str] = None
    """The model that generated this chunk."""

    finish_reason: Optional[str] = None
    """The reason the stream finished (if applicable)."""

    chunk: Optional[Any] = None
    """The original chunk object from the provider."""

    is_final: bool = False
    """Whether this is the final chunk in the stream."""

    def __bool__(self) -> bool:
        """Check if this chunk has meaningful content."""
        return bool(self.content or self.output or self.finish_reason)

    def __str__(self) -> str:
        """String representation of the chunk."""
        if self.output:
            return f"LanguageModelResponseChunk(output={self.output})"
        elif self.content:
            return f"LanguageModelResponseChunk(content={repr(self.content)})"
        elif self.finish_reason:
            return f"LanguageModelResponseChunk(finish_reason={self.finish_reason})"
        else:
            return "LanguageModelResponseChunk(empty)"
