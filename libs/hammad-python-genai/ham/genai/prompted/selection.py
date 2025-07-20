"""ham.genai.prompted.selection

Selection strategies for graph chaining and conditional routing.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

try:
    from ham.core.logging.logger import _get_internal_logger
except ImportError:
    from ...logging.logger import _get_internal_logger  # type: ignore

from ..models.language.model import LanguageModel
from pydantic import BaseModel, Field, create_model

__all__ = [
    "SelectionStrategy",
    "select",
]

logger = _get_internal_logger(__name__)


class SelectionStrategy:
    """LLM-based selection strategy for choosing the next function in a chain."""

    def __init__(
        self,
        *functions: Union[str, Callable],
        instructions: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.functions = list(functions)
        self.instructions = instructions
        self.model = model or "openai/gpt-4o-mini"
        self._language_model = None
        self._use_all_functions = (
            len(functions) == 0
        )  # If no functions specified, use all available

    def _get_language_model(self):
        """Lazy load the language model."""
        if self._language_model is None:
            self._language_model = LanguageModel(model=self.model)
        return self._language_model

    def select(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to select the most appropriate function."""
        if not context:
            context = {}

        # Get available functions
        functions_to_choose_from = self.functions
        if self._use_all_functions and "all_functions" in context:
            # Use all available functions from the caller
            functions_to_choose_from = context["all_functions"]

        if not functions_to_choose_from:
            return ""

        # If only one function, return it
        if len(functions_to_choose_from) == 1:
            func = functions_to_choose_from[0]
            return func.__name__ if callable(func) else str(func)

        # Create enum for available functions
        function_names = []
        for func in functions_to_choose_from:
            if callable(func):
                function_names.append(func.__name__)
            else:
                function_names.append(str(func))

        FunctionEnum = Enum("FunctionEnum", {name: name for name in function_names})

        # Create selection model
        SelectionModel = create_model(
            "FunctionSelection",
            function=(
                FunctionEnum,
                Field(description="The selected function to execute next"),
            ),
            reasoning=(str, Field(description="Brief reasoning for the selection")),
        )

        # Build context description
        context_parts = []

        # Add result from previous function
        if "result" in context:
            context_parts.append(f"Previous function result: {context['result']}")

        # Add conversation history
        if "messages" in context and context["messages"]:
            # Get last few messages for context
            recent_messages = context["messages"][-5:]  # Last 5 messages
            messages_str = "\n".join(
                [
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in recent_messages
                ]
            )
            context_parts.append(f"Recent conversation:\n{messages_str}")

        # Add state information
        if "state" in context and context["state"]:
            context_parts.append(f"Current state: {context['state']}")

        context_description = "\n\n".join(context_parts)

        # Build selection prompt
        base_instructions = f"""Based on the context below, select the most appropriate next function from the available options.

Available functions:
{", ".join(function_names)}

Context:
{context_description}

Consider the conversation flow, user's request, and any patterns in the conversation when making your selection."""

        # Add custom instructions if provided
        if self.instructions:
            base_instructions = (
                f"{base_instructions}\n\nAdditional instructions:\n{self.instructions}"
            )

        # Get language model to make selection
        try:
            lm = self._get_language_model()
            response = lm.run(
                messages=[{"role": "user", "content": base_instructions}],
                type=SelectionModel,
            )

            selected_function = response.output.function.value

            # Validate the selection
            if selected_function in function_names:
                return selected_function
            else:
                # Fallback to first function if invalid selection
                return function_names[0]

        except Exception as e:
            logger.warning(f"Selection strategy failed: {e}")
            # Fallback to first function on any error
            return function_names[0] if function_names else ""

    def __repr__(self) -> str:
        if self._use_all_functions:
            return "SelectionStrategy(all_functions)"
        function_names = [f.__name__ if callable(f) else str(f) for f in self.functions]
        return f"SelectionStrategy({', '.join(repr(n) for n in function_names)})"


def select(
    *functions: Union[str, Callable],
    instructions: Optional[str] = None,
    model: Optional[str] = None,
) -> SelectionStrategy:
    """
    Create an LLM-based selection strategy for choosing between multiple functions.

    Args:
        *functions: The functions to choose from. If empty, will select from all available.
        instructions: Optional instructions for the LLM selection
        model: Optional model to use for selection (defaults to gpt-4o-mini)

    Returns:
        A SelectionStrategy instance

    Examples:
        Select between specific functions:
        ```python
        @prompted
        def reasoning(message: str) -> str:
            pass

        @prompted
        def response(message: str) -> str:
            pass

        # Chain with selection
        chained = reasoning.next(select(response, reasoning))
        ```

        Select from all available functions:
        ```python
        @prompted
        def analyze(text: str) -> str:
            pass

        # Will select from all functions in scope
        flexible = analyze.next(select())
        ```

        With custom instructions:
        ```python
        strategy = select(
            reasoning, response,
            instructions="If the user asked for multiple reasonings, select 'reasoning' again"
        )
        ```
    """
    return SelectionStrategy(*functions, instructions=instructions, model=model)
