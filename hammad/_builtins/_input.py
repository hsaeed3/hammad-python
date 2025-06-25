"""hammad._builtins._input"""

import json
from typing import Any, Dict, List, Optional, Union, overload

from rich import get_console
from rich.console import Console
from rich.prompt import Prompt, Confirm
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.completion import WordCompleter

from ._internal._style_types import (
    StyleColorName,
    StyleStyleSettings,
    StyleBackgroundSettings,
)
from ._internal._style_utils import wrap_renderable_with_styles


class InputError(Exception):
    """Exception raised for errors in the Input module."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


def _validate_against_schema(value: str, schema: Any) -> Any:
    """Validate and convert input value against a schema.

    Args:
        value: The input value as a string.
        schema: The schema to validate against.

    Returns:
        The converted/validated value.

    Raises:
        InputError: If validation fails.
    """
    if schema is None:
        return value

    try:
        # Handle basic types
        if schema == str:
            return value
        elif schema == int:
            return int(value)
        elif schema == float:
            return float(value)
        elif schema == bool:
            return value.lower() in ("true", "t", "yes", "y", "1", "on")

        # Handle dict - expect JSON input
        elif schema == dict or (
            hasattr(schema, "__origin__") and schema.__origin__ is dict
        ):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise InputError(f"Invalid JSON format for dictionary input")

        # Handle list - expect JSON input
        elif schema == list or (
            hasattr(schema, "__origin__") and schema.__origin__ is list
        ):
            try:
                result = json.loads(value)
                if not isinstance(result, list):
                    raise InputError("Expected a list")
                return result
            except json.JSONDecodeError:
                raise InputError(f"Invalid JSON format for list input")

        # Handle Union types (including Optional)
        elif hasattr(schema, "__origin__") and schema.__origin__ is Union:
            args = schema.__args__
            if len(args) == 2 and type(None) in args:
                # This is Optional[T]
                if not value or value.lower() == "none":
                    return None
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return _validate_against_schema(value, non_none_type)

        # Handle Pydantic models
        elif hasattr(schema, "model_validate_json"):
            try:
                return schema.model_validate_json(value)
            except Exception as e:
                raise InputError(f"Invalid input for {schema.__name__}: {e}")

        # Handle BasedModels
        elif hasattr(schema, "model_validate_json") or (
            hasattr(schema, "__bases__")
            and any("BasedModel" in str(base) for base in schema.__bases__)
        ):
            try:
                return schema.model_validate_json(value)
            except Exception as e:
                raise InputError(f"Invalid input for {schema.__name__}: {e}")

        # Handle dataclasses
        elif hasattr(schema, "__dataclass_fields__"):
            try:
                data = json.loads(value)
                return schema(**data)
            except Exception as e:
                raise InputError(f"Invalid input for {schema.__name__}: {e}")

        # Handle TypedDict
        elif hasattr(schema, "__annotations__") and hasattr(schema, "__total__"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise InputError(f"Invalid JSON format for {schema.__name__}")

        # Fallback - try to parse as JSON
        else:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

    except InputError:
        raise
    except Exception as e:
        raise InputError(f"Validation error: {e}")


def _collect_fields_sequentially(schema: Any, console: Console) -> Dict[str, Any]:
    """Collect field values sequentially for structured schemas.

    Args:
        schema: The schema to collect fields for.
        console: The console to use for output.

    Returns:
        Dictionary of field names to values.
    """
    result = {}

    try:
        # Handle Pydantic models
        if hasattr(schema, "model_fields"):
            fields_info = schema.model_fields
            console.print(
                f"\n[bold blue]Entering data for {schema.__name__}:[/bold blue]"
            )

            for field_name, field_info in fields_info.items():
                field_type = (
                    field_info.annotation if hasattr(field_info, "annotation") else str
                )
                default = getattr(field_info, "default", None)

                prompt_text = f"  {field_name}"
                if default is not None and default != "...":
                    prompt_text += f" (default: {default})"
                prompt_text += ": "

                value = Prompt.ask(prompt_text)
                if not value and default is not None and default != "...":
                    result[field_name] = default
                else:
                    try:
                        result[field_name] = _validate_against_schema(value, field_type)
                    except InputError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        result[field_name] = value

        # Handle BasedModels
        elif hasattr(schema, "_get_fields_info"):
            fields_info = schema._get_fields_info()
            console.print(
                f"\n[bold blue]Entering data for {schema.__name__}:[/bold blue]"
            )

            for field_name, field_info in fields_info.items():
                field_type = field_info.get("type", str)
                default = field_info.get("default")
                required = field_info.get("required", True)

                prompt_text = f"  {field_name}"
                if not required and default is not None:
                    prompt_text += f" (default: {default})"
                elif not required:
                    prompt_text += " (optional)"
                prompt_text += ": "

                value = Prompt.ask(prompt_text)
                if not value and not required and default is not None:
                    result[field_name] = default
                elif not value and not required:
                    continue
                else:
                    try:
                        result[field_name] = _validate_against_schema(value, field_type)
                    except InputError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        result[field_name] = value

        # Handle dataclasses
        elif hasattr(schema, "__dataclass_fields__"):
            fields_info = schema.__dataclass_fields__
            console.print(
                f"\n[bold blue]Entering data for {schema.__name__}:[/bold blue]"
            )

            for field_name, field_info in fields_info.items():
                field_type = field_info.type
                default = getattr(field_info, "default", None)

                prompt_text = f"  {field_name}"
                if default is not None:
                    prompt_text += f" (default: {default})"
                prompt_text += ": "

                value = Prompt.ask(prompt_text)
                if not value and default is not None:
                    result[field_name] = default
                else:
                    try:
                        result[field_name] = _validate_against_schema(value, field_type)
                    except InputError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        result[field_name] = value

        # Handle TypedDict
        elif hasattr(schema, "__annotations__"):
            annotations = getattr(schema, "__annotations__", {})
            console.print(
                f"\n[bold blue]Entering data for {schema.__name__}:[/bold blue]"
            )

            for field_name, field_type in annotations.items():
                prompt_text = f"  {field_name}: "
                value = Prompt.ask(prompt_text)

                if value:
                    try:
                        result[field_name] = _validate_against_schema(value, field_type)
                    except InputError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        result[field_name] = value

    except Exception as e:
        console.print(f"[red]Error collecting fields: {e}[/red]")

    return result


@overload
def input(prompt: str = "") -> str: ...


@overload
def input(
    prompt: str = "",
    schema: Any = None,
    sequential: bool = True,
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
    multiline: bool = False,
    password: bool = False,
    complete: Optional[List[str]] = None,
    validate: Optional[callable] = None,
) -> Any: ...


def input(
    prompt: str = "",
    schema: Any = None,
    sequential: bool = True,
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
    multiline: bool = False,
    password: bool = False,
    complete: Optional[List[str]] = None,
    validate: Optional[callable] = None,
) -> Any:
    """
    Stylized input function built with `rich` and `prompt_toolkit`. This method maintains
    compatibility with the standard input function while adding advanced features like
    schema validation, styling, and structured data input.

    Args:
        prompt: The prompt message to display.
        schema: A type, model class, or schema to validate against. Supports:
            - Basic types (str, int, float, bool)
            - Collections (dict, list)
            - Pydantic models
            - BasedModels
            - Dataclasses
            - TypedDict
        sequential: For schemas with multiple fields, request one field at a time.
        style: A color or dictionary of style settings to apply to the prompt.
        bg: A color or dictionary of background settings to apply to the prompt.
        multiline: Whether to allow multiline input.
        password: Whether to hide the input (password mode).
        complete: List of completion options.
        validate: Custom validation function.

    Returns:
        The validated input value, converted to the appropriate type based on schema.

    Raises:
        InputError: If validation fails or input is invalid.
    """
    console = get_console()

    try:
        # If no special features are requested, use built-in input for compatibility
        if (
            schema is None
            and style is None
            and bg is None
            and not multiline
            and not password
            and complete is None
            and validate is None
        ):
            import builtins

            return builtins.input(prompt)

        # Apply styling to prompt if provided
        styled_prompt = wrap_renderable_with_styles(prompt, style=style, background=bg)

        # Handle schema-based input
        if schema is not None:
            # Handle bool schema with Confirm.ask
            if schema == bool:
                return Confirm.ask(styled_prompt)

            # Handle structured schemas with multiple fields
            if sequential and (
                hasattr(schema, "__annotations__")
                or hasattr(schema, "model_fields")
                or hasattr(schema, "_get_fields_info")
                or hasattr(schema, "__dataclass_fields__")
            ):
                field_data = _collect_fields_sequentially(schema, console)

                try:
                    # Create instance from collected data
                    if hasattr(schema, "model_validate"):
                        # Pydantic model
                        return schema.model_validate(field_data)
                    elif hasattr(schema, "__call__"):
                        # BasedModel, dataclass, or other callable
                        return schema(**field_data)
                    else:
                        # TypedDict or similar - return the dict
                        return field_data
                except Exception as e:
                    console.print(f"[red]Error creating {schema.__name__}: {e}[/red]")
                    return field_data

        # Handle single value input
        if password:
            value = Prompt.ask(styled_prompt, password=True)
        elif complete:
            # Use prompt_toolkit for completion
            completer = WordCompleter(complete)
            value = pt_prompt(str(styled_prompt), completer=completer)
        elif multiline:
            console.print(styled_prompt, end="")
            lines = []
            console.print("[dim](Enter empty line to finish)[/dim]")
            while True:
                line = pt_prompt("... ")
                if not line:
                    break
                lines.append(line)
            value = "\n".join(lines)
        else:
            # Regular input with Rich prompt
            value = Prompt.ask(styled_prompt)

        # Apply custom validation
        if validate:
            try:
                if not validate(value):
                    raise InputError("Custom validation failed")
            except Exception as e:
                raise InputError(f"Validation error: {e}")

        # Apply schema validation
        if schema is not None:
            return _validate_against_schema(value, schema)

        return value

    except KeyboardInterrupt:
        console.print("\n[yellow]Input cancelled by user[/yellow]")
        raise
    except InputError:
        raise
    except Exception as e:
        raise InputError(f"Input error: {e}")


# Convenience functions for specific input types
def input_int(
    prompt: str = "Enter an integer: ",
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
) -> int:
    """Get integer input with validation."""
    return input(prompt, schema=int, style=style, bg=bg)


def input_float(
    prompt: str = "Enter a number: ",
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
) -> float:
    """Get float input with validation."""
    return input(prompt, schema=float, style=style, bg=bg)


def input_bool(
    prompt: str = "Enter yes/no: ",
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
) -> bool:
    """Get boolean input with validation."""
    return input(prompt, schema=bool, style=style, bg=bg)


def input_json(
    prompt: str = "Enter JSON: ",
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
) -> Dict[str, Any]:
    """Get JSON input with validation."""
    return input(prompt, schema=dict, style=style, bg=bg)


def input_confirm(
    prompt: str = "Continue?",
    default: bool = False,
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
) -> bool:
    """Get confirmation input (yes/no)."""
    styled_prompt = wrap_renderable_with_styles(prompt, style=style, background=bg)
    return Confirm.ask(styled_prompt, default=default)
