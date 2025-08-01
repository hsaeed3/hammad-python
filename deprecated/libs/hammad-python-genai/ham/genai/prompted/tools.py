"""ham.genai.prompted.tools

Tool creation and management for the prompted framework.
"""

from typing import Any, Callable, List, Optional, TypeVar, Union, ParamSpec
from ..types.tools import Tool, define_tool as _define_tool

__all__ = [
    "tool",
    "define_tool",
]

P = ParamSpec("P")
R = TypeVar("R")


def tool(
    func: Optional[Callable[P, R]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    takes_context: bool = False,
    strict: bool = True,
) -> Union[Tool, Callable[[Callable[P, R]], Tool]]:
    """
    Decorator to create a tool that can be used by prompted functions.

    This is a convenience wrapper around the core tool definition functionality,
    designed specifically for the prompted framework.

    Args:
        func: Function to wrap (when used as @tool)
        name: Override tool name (defaults to function name)
        description: Override tool description (defaults to function docstring)
        takes_context: Whether function expects context as first parameter
        strict: Whether to enforce strict JSON schema validation

    Returns:
        Tool instance or decorator function

    Examples:
        Basic tool:
        ```python
        @tool
        def search_web(query: str) -> str:
            "Search the web for information."
            # Implementation here
            return f"Search results for: {query}"

        @prompted(tools=[search_web])
        def research(topic: str) -> str:
            "Research the given topic using web search."
        ```

        Tool with custom name and description:
        ```python
        @tool(name="calculator", description="Perform mathematical calculations")
        def calc(expression: str) -> float:
            return eval(expression)  # In practice, use safe evaluation
        ```

        Tool that takes context:
        ```python
        @tool(takes_context=True)
        def get_user_info(context, field: str) -> str:
            "Get information about the current user."
            return context.user_data.get(field, "Unknown")
        ```
    """

    def decorator(f: Callable[P, R]) -> Tool:
        return _define_tool(
            f,
            name=name,
            description=description,
            takes_context=takes_context,
            strict=strict,
        )

    if func is None:
        return decorator
    else:
        return decorator(func)


# Alias for consistency with the core framework
define_tool = tool
