"""hammad.genai.types.tool

Tool system for agent function calling with JSON schema generation.
"""

import asyncio
import concurrent.futures
from dataclasses import dataclass
import inspect
import json
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    get_type_hints,
    TYPE_CHECKING,
    Generic,
    TypeVar,
    ParamSpec,
    overload,
)
from pydantic import BaseModel, Field, ValidationError

from ...formatting.json.converters import convert_to_json_schema
from ...data.models.extensions.pydantic.converters import (
    get_pydantic_fields_from_function,
    convert_to_pydantic_model,
)
from .base import BaseGenAIModelStream, BaseGenAIModelResponse, BaseTool


# Type variables for generic tool typing
P = ParamSpec("P")
R = TypeVar("R")

__all__ = (
    "Tool",
    "define_tool",
    "ToolResponseMessage",
    "execute_tool_calls_parallel",
    "execute_tools_from_language_model_response",
)


@dataclass
class ToolResponseMessage:
    """Represents a tool response message for chat completion."""

    tool_call_id: str
    """ID of the tool call this response corresponds to."""

    name: str
    """Name of the tool that was called."""

    content: str
    """The result/output of the tool execution."""

    role: str = "tool"
    """Message role, always 'tool'."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API calls."""
        return {
            "role": self.role,
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }


def extract_tool_calls_from_response(
    response: Union["BaseGenAIModelResponse", "BaseGenAIModelStream"],
) -> List[Any]:
    """Extract tool calls from various response types."""
    # ensure type is of agent or language model
    if response.type not in ["language_model", "agent", "graph"]:
        raise ValueError(f"Response type {response.type} is not supported")

    # Handle LanguageModelResponse
    if hasattr(response, "get_tool_calls"):
        tool_calls = response.get_tool_calls()
        return tool_calls or []

    # Handle Stream/AsyncStream - need to collect first
    if hasattr(response, "collect"):
        try:
            if hasattr(response, "_is_consumed") and not response._is_consumed:
                # For streams, we need to consume them first
                if asyncio.iscoroutine(response.collect()):
                    # Async stream
                    loop = asyncio.get_event_loop()
                    collected_response = loop.run_until_complete(response.collect())
                else:
                    # Sync stream
                    collected_response = response.collect()

                if hasattr(collected_response, "get_tool_calls"):
                    return collected_response.get_tool_calls() or []
            else:
                # Already consumed, try to get tool calls directly
                if hasattr(response, "get_tool_calls"):
                    return response.get_tool_calls() or []
        except Exception:
            pass

    # Check if response has tool_calls attribute directly
    if hasattr(response, "tool_calls"):
        return response.tool_calls or []

    return []


def execute_tool_calls_parallel(
    tool: "Tool", tool_calls: List[Any], context: Any = None
) -> List[ToolResponseMessage]:
    """Execute multiple tool calls in parallel using ThreadPoolExecutor."""
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(tool_calls), 4)
    ) as executor:
        futures = [
            executor.submit(tool.call_from_tool_call, call, context)
            for call in tool_calls
        ]

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                # Create error response
                results.append(
                    ToolResponseMessage(
                        tool_call_id="unknown",
                        name=tool.name,
                        content=f"Tool execution failed: {str(e)}",
                    )
                )

        return results


class Tool(BaseTool[P, R]):
    """A tool that wraps a function for agent execution.

    Combines concepts from both PydanticAI and OpenAI tool specifications
    to provide a simple, internalized tool system.
    """

    takes_context: bool = Field(
        default=False,
        description="Whether the function expects a context as first parameter.",
    )
    """Whether the function expects a context as first parameter."""

    strict: bool = Field(
        default=True, description="Whether to enforce strict JSON schema validation."
    )
    """Whether to enforce strict JSON schema validation."""

    def model_post_init(self, __context: Any) -> None:
        """Validate the tool after initialization."""
        if not callable(self.function):
            raise ValueError("Tool function must be callable")
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.parameters_json_schema:
            raise ValueError("Tool must have parameters JSON schema")

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Call the tool's function directly with the given arguments.

        This allows using the tool as if it were the original function.

        Args:
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call
        """
        return self.function(*args, **kwargs)

    def call(
        self,
        arguments: Union[str, Dict[str, Any]],
        context: Any = None,
    ) -> Any:
        """Execute the tool with given arguments.

        Args:
            arguments: Tool arguments as JSON string or dict
            context: Optional context to pass as first argument if takes_context=True
            as_message: Whether to return the result as a ToolResponseMessage

        Returns:
            The result of the function call

        Raises:
            ValidationError: If arguments don't match schema
            ValueError: If function execution fails
        """
        # Parse arguments if they're a JSON string
        if isinstance(arguments, str):
            try:
                args_dict = json.loads(arguments)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON arguments: {e}")
        else:
            args_dict = arguments or {}

        # Get function signature and validate arguments
        sig = inspect.signature(self.function)

        # Filter out context parameter if needed
        if self.takes_context:
            params = {
                k: v
                for k, v in sig.parameters.items()
                if k not in ("self", "cls", "context", "ctx")
            }
            filtered_sig = sig.replace(parameters=list(params.values()))
            bound_args = filtered_sig.bind_partial(**args_dict)
        else:
            bound_args = sig.bind_partial(**args_dict)

        try:
            bound_args.apply_defaults()
        except TypeError as e:
            raise ValidationError(f"Arguments don't match function signature: {e}")

        # Execute function with or without context
        try:
            if self.takes_context:
                return self.function(context, **bound_args.arguments)
            else:
                return self.function(**bound_args.arguments)
        except Exception as e:
            raise ValueError(f"Tool execution failed: {e}")

    def call_from_tool_call(
        self, tool_call: Union[Dict[str, Any], Any], context: Any = None
    ) -> ToolResponseMessage:
        """Execute tool from a tool call and return a tool response message.

        Args:
            tool_call: Tool call dict or object with function.arguments and id
            context: Optional context to pass to function

        Returns:
            ToolResponseMessage with tool call ID and result
        """
        # Extract tool call information
        if isinstance(tool_call, dict):
            tool_call_id = tool_call.get("id") or tool_call.get(
                "tool_call_id", "unknown"
            )
            if "function" in tool_call:
                arguments = tool_call["function"].get("arguments", "{}")
            else:
                arguments = tool_call.get("arguments", "{}")
        else:
            # Assume it's a pydantic object or similar
            tool_call_id = getattr(tool_call, "id", "unknown")
            if hasattr(tool_call, "function"):
                arguments = getattr(tool_call.function, "arguments", "{}")
            else:
                arguments = getattr(tool_call, "arguments", "{}")

        # Execute the tool
        try:
            result = self.call(arguments, context)
            content = (
                str(result) if result is not None else "Tool executed successfully"
            )
        except Exception as e:
            content = f"Tool execution failed: {str(e)}"

        return ToolResponseMessage(
            tool_call_id=tool_call_id, name=self.name, content=content
        )

    def call_from_response(
        self,
        response: Union["BaseGenAIModelResponse", "BaseGenAIModelStream"],
        context: Any = None,
        parallel: bool = True,
    ) -> List[ToolResponseMessage]:
        """Execute tool calls found in a language model response or stream.

        Args:
            response: LanguageModelResponse, Stream, or AsyncStream
            context: Optional context to pass to functions
            parallel: Whether to execute tool calls in parallel

        Returns:
            List of ToolResponseMessage objects
        """
        tool_calls = extract_tool_calls_from_response(response)

        if not tool_calls:
            return []

        # Filter tool calls that match this tool's name
        matching_calls = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                func_name = tool_call.get("function", {}).get("name")
            else:
                func_name = (
                    getattr(tool_call.function, "name", None)
                    if hasattr(tool_call, "function")
                    else None
                )

            if func_name == self.name:
                matching_calls.append(tool_call)

        if not matching_calls:
            return []

        if parallel and len(matching_calls) > 1:
            return execute_tool_calls_parallel(self, matching_calls, context)
        else:
            return [self.call_from_tool_call(call, context) for call in matching_calls]

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format suitable for API calls."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_json_schema,
                "strict": self.strict,
            },
        }


@overload
def define_tool(
    function: Callable[P, R],
) -> Tool:
    """Overload for direct decorator usage: @define_tool"""
    ...


@overload
def define_tool(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    takes_context: bool = False,
    strict: bool = True,
) -> Callable[[Callable[P, R]], Tool]:
    """Overload for decorator with parameters: @define_tool(...)"""
    ...


def define_tool(
    function: Optional[Callable[P, R]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    takes_context: bool = False,
    strict: bool = True,
) -> Union[Tool, Callable[[Callable[P, R]], Tool]]:
    """Decorator to create a Tool from a function.

    Args:
        func: Function to wrap (when used as @define_tool)
        name: Override tool name (defaults to function name)
        description: Override tool description (defaults to function docstring)
        takes_context: Whether function expects context as first parameter
        strict: Whether to enforce strict JSON schema validation

    Returns:
        Tool instance or decorator function

    Example:
        @define_tool
        def my_tool(x: int, y: str = "default") -> str:
            \"\"\"Does something useful.\"\"\"
            return f"{x}: {y}"

        # Or with parameters:
        @define_tool(name="custom_name", takes_context=True)
        def context_tool(ctx, value: int) -> int:
            return value * 2
    """

    def _create_tool(target_func: Callable[P, R]) -> Tool:
        # Extract function metadata
        func_name = name or target_func.__name__
        func_description = description or (target_func.__doc__ or "").strip()

        # Generate JSON schema from function signature
        try:
            # Try using Pydantic converter first for better schema generation
            pydantic_fields = get_pydantic_fields_from_function(target_func)
            if pydantic_fields:
                # Create temporary Pydantic model to get schema
                temp_model = convert_to_pydantic_model(
                    target_func, name=f"{func_name}_params"
                )
                schema = temp_model.model_json_schema()
                # Extract just the properties and required fields
                parameters_schema = {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                }
                if "required" in schema:
                    parameters_schema["required"] = schema["required"]
                if strict:
                    parameters_schema["additionalProperties"] = False
            else:
                # Fallback to basic JSON schema conversion
                parameters_schema = _generate_schema_from_signature(target_func, strict)
        except Exception:
            # Ultimate fallback
            parameters_schema = _generate_schema_from_signature(target_func, strict)

        return Tool(
            name=func_name,
            description=func_description,
            function=target_func,
            parameters_json_schema=parameters_schema,
            takes_context=takes_context,
            strict=strict,
        )

    # Handle decorator usage patterns
    if function is None:
        # Used as @define_tool(...)
        return _create_tool
    else:
        # Used as @define_tool
        return _create_tool(function)


def _generate_schema_from_signature(
    func: Callable, strict: bool = True
) -> Dict[str, Any]:
    """Generate JSON schema from function signature as fallback."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == "self" or param_name == "cls":
            continue

        param_type = type_hints.get(param_name, str)

        try:
            # Use JSON converter for type
            param_schema = convert_to_json_schema(param_type)
        except Exception:
            # Ultimate fallback
            param_schema = {"type": "string"}

        properties[param_name] = param_schema

        # Add to required if no default value
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    if strict:
        schema["additionalProperties"] = False

    return schema


# Utility functions for batch tool execution
def execute_tools_from_language_model_response(
    tools: List[Tool],
    response: Union["BaseGenAIModelResponse", "BaseGenAIModelStream"],
    context: Any = None,
    parallel: bool = True,
) -> List[ToolResponseMessage]:
    """Execute all matching tools from a response.

    Args:
        tools: List of tools to check for matches
        response: LanguageModelResponse, Stream, or AsyncStream
        context: Optional context to pass to functions
        parallel: Whether to execute tool calls in parallel

    Returns:
        List of ToolResponseMessage objects from all executed tools
    """
    all_results = []
    for tool in tools:
        results = tool.call_from_response(response, context, parallel)
        all_results.extend(results)
    return all_results
