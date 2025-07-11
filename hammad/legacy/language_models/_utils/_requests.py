"""hammad.genai.language_models._utils._requests"""

from typing import (
    Any,
    Dict,
    List,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
    TYPE_CHECKING,
)

from ....data.models import (
    convert_to_pydantic_model,
    is_pydantic_model_class,
)

from .._types import LanguageModelName, LanguageModelInstructorMode
from ..language_model_request import (
    LanguageModelMessagesParam,
    LanguageModelRequest,
)

__all__ = [
    "LanguageModelRequestBuilder"
]


T = TypeVar("T")


class LanguageModelRequestBuilder(Generic[T]):
    """A request to a language model with comprehensive parameter handling."""
    
    def __init__(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        model: LanguageModelName = "openai/gpt-4o-mini",
        **kwargs: Any,
    ):
        """Initialize a language model request.
        
        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            model: The model to use for the request
            **kwargs: Additional request settings
        """
        self.messages = messages
        self.instructions = instructions
        self.model = model
        self.settings = self._build_settings(**kwargs)
        
        # Validate settings
        self._validate_settings()
    
    def _build_settings(self, **kwargs: Any) -> LanguageModelRequest:
        """Build the complete settings dictionary from kwargs."""
        settings: LanguageModelRequest = {"model": self.model}
        
        # Add all provided kwargs to settings
        for key, value in kwargs.items():
            if value is not None:
                settings[key] = value
        
        return settings
    
    def _validate_settings(self) -> None:
        """Validate that the settings are compatible."""
        # Check if both tools and structured outputs are specified
        has_tools = any(
            key in self.settings
            for key in ["tools", "tool_choice", "parallel_tool_calls", "functions", "function_call"]
        )
        
        has_structured_output = "type" in self.settings and self.settings["type"] is not str
        
        if has_tools and has_structured_output:
            raise ValueError(
                "Tools and structured outputs cannot be used together. "
                "Please specify either tools OR a structured output type, not both."
            )
    
    def is_structured_output(self) -> bool:
        """Check if this request is for structured output."""
        return "type" in self.settings and self.settings["type"] is not str
    
    def is_streaming(self) -> bool:
        """Check if this request is for streaming."""
        return self.settings.get("stream", False)
    
    def has_tools(self) -> bool:
        """Check if this request has tools."""
        return any(
            key in self.settings
            for key in ["tools", "tool_choice", "parallel_tool_calls", "functions", "function_call"]
        )
    
    def get_completion_settings(self) -> Dict[str, Any]:
        """Get settings filtered for standard completion requests."""
        excluded_keys = {
            "type", "instructor_mode", "response_field_name", 
            "response_field_instruction", "response_model_name", "max_retries", "strict",
            "validation_context", "context",
            "completion_kwargs_hooks", "completion_response_hooks", 
            "completion_error_hooks", "completion_last_attempt_hooks", 
            "parse_error_hooks"
        }
        
        return {
            key: value for key, value in self.settings.items()
            if key not in excluded_keys
        }
    
    def get_structured_output_settings(self) -> Dict[str, Any]:
        """Get settings filtered for structured output requests."""
        excluded_keys = {
            "tools", "tool_choice", "parallel_tool_calls", 
            "functions", "function_call",
            "type", "instructor_mode", "response_field_name", 
            "response_field_instruction", "response_model_name", "max_retries", "strict",
            "validation_context", "context",
            "completion_kwargs_hooks", "completion_response_hooks", 
            "completion_error_hooks", "completion_last_attempt_hooks", 
            "parse_error_hooks"
        }
        
        return {
            key: value for key, value in self.settings.items()
            if key not in excluded_keys
        }
    
    def get_output_type(self) -> Type[T]:
        """Get the requested output type."""
        return self.settings.get("type", str)
    
    def get_instructor_mode(self) -> LanguageModelInstructorMode:
        """Get the instructor mode for structured outputs."""
        return self.settings.get("instructor_mode", "tool_call")
    
    def get_response_field_name(self) -> str:
        """Get the response field name for structured outputs."""
        return self.settings.get("response_field_name", "content")
    
    def get_response_field_instruction(self) -> str:
        """Get the response field instruction for structured outputs."""
        return self.settings.get(
            "response_field_instruction",
            "A response in the correct type as requested by the user, or relevant content."
        )
    
    def get_response_model_name(self) -> str:
        """Get the response model name for structured outputs."""
        return self.settings.get("response_model_name", "Response")
    
    def get_max_retries(self) -> int:
        """Get the maximum retries for structured outputs."""
        return self.settings.get("max_retries", 3)
    
    def get_strict_mode(self) -> bool:
        """Get the strict mode for structured outputs."""
        return self.settings.get("strict", True)
    
    def get_validation_context(self) -> Optional[Dict[str, Any]]:
        """Get the validation context for structured outputs."""
        return self.settings.get("validation_context")
    
    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get the context for structured outputs."""
        return self.settings.get("context")
    
    def prepare_pydantic_model(self) -> Optional[Type[Any]]:
        """Prepare a Pydantic model for structured outputs if needed."""
        if not self.is_structured_output():
            return None
        
        output_type = self.get_output_type()

        if is_pydantic_model_class(output_type):
            return output_type
        
        # Convert to Pydantic model
        return convert_to_pydantic_model(
            target=output_type,
            name="Response",
            field_name=self.get_response_field_name(),
            description=self.get_response_field_instruction(),
        )
    
    def __repr__(self) -> str:
        """String representation of the request."""
        return (
            f"LanguageModelRequest("
            f"model={self.model}, "
            f"structured_output={self.is_structured_output()}, "
            f"streaming={self.is_streaming()}, "
            f"has_tools={self.has_tools()}"
            f")"
        )