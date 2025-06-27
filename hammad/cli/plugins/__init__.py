"""hammad.cli.plugins

Contains the following 'builtin' plugins or extensions:

- `print()`
- `input()`
- `animate()`
"""

from __future__ import annotations

import builtins
import json
from typing import (
    Optional,
    IO,
    overload,
    Any,
    Dict,
    Literal,
    List,
    Union,
    Callable,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from rich import get_console
    from rich.console import Console, RenderableType
    from rich.prompt import Prompt, Confirm
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter
    from ..styles.animations import (
        CLIFlashingAnimation,
        CLIPulsingAnimation,
        CLIShakingAnimation,
        CLITypingAnimation,
        CLISpinningAnimation,
        CLIRainbowAnimation,
        RainbowPreset,
    )
    from ..styles.types import (
        CLIStyleType,
        CLIStyleBackgroundType,
        CLIStyleColorName,
    )
    from ..styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )
    from ..styles.utils import (
        live_render,
        style_renderable,
    )

# Lazy import cache
_IMPORT_CACHE = {}


def _get_rich_console():
    """Lazy import for rich.get_console"""
    if "get_console" not in _IMPORT_CACHE:
        from rich import get_console

        _IMPORT_CACHE["get_console"] = get_console
    return _IMPORT_CACHE["get_console"]


def _get_rich_console_classes():
    """Lazy import for rich.console classes"""
    if "console_classes" not in _IMPORT_CACHE:
        from rich.console import Console, RenderableType

        _IMPORT_CACHE["console_classes"] = (Console, RenderableType)
    return _IMPORT_CACHE["console_classes"]


def _get_rich_prompts():
    """Lazy import for rich.prompt classes"""
    if "prompts" not in _IMPORT_CACHE:
        from rich.prompt import Prompt, Confirm

        _IMPORT_CACHE["prompts"] = (Prompt, Confirm)
    return _IMPORT_CACHE["prompts"]


def _get_prompt_toolkit():
    """Lazy import for prompt_toolkit"""
    if "prompt_toolkit" not in _IMPORT_CACHE:
        from prompt_toolkit import prompt as pt_prompt
        from prompt_toolkit.completion import WordCompleter

        _IMPORT_CACHE["prompt_toolkit"] = (pt_prompt, WordCompleter)
    return _IMPORT_CACHE["prompt_toolkit"]


def _get_style_utils():
    """Lazy import for style utilities"""
    if "style_utils" not in _IMPORT_CACHE:
        from ..styles.utils import live_render, style_renderable

        _IMPORT_CACHE["style_utils"] = (live_render, style_renderable)
    return _IMPORT_CACHE["style_utils"]


def _get_animation_classes():
    """Lazy import for animation classes"""
    if "animations" not in _IMPORT_CACHE:
        from ..styles.animations import (
            CLIFlashingAnimation,
            CLIPulsingAnimation,
            CLIShakingAnimation,
            CLITypingAnimation,
            CLISpinningAnimation,
            CLIRainbowAnimation,
            RainbowPreset,
        )

        _IMPORT_CACHE["animations"] = {
            "CLIFlashingAnimation": CLIFlashingAnimation,
            "CLIPulsingAnimation": CLIPulsingAnimation,
            "CLIShakingAnimation": CLIShakingAnimation,
            "CLITypingAnimation": CLITypingAnimation,
            "CLISpinningAnimation": CLISpinningAnimation,
            "CLIRainbowAnimation": CLIRainbowAnimation,
            "RainbowPreset": RainbowPreset,
        }
    return _IMPORT_CACHE["animations"]


@overload
def print(
    *values: object,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
) -> None: ...


@overload
def print(
    *values: object,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
    style: "CLIStyleType | None" = None,
    style_settings: "CLIStyleRenderableSettings | None" = None,
    bg: "CLIStyleBackgroundType | None" = None,
    bg_settings: "CLIStyleBackgroundSettings | None" = None,
    live: "CLIStyleLiveSettings | int | None" = None,
) -> None: ...


def print(
    *values: object,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
    style: "CLIStyleType | None" = None,
    style_settings: "CLIStyleRenderableSettings | None" = None,
    bg: "CLIStyleBackgroundType | None" = None,
    bg_settings: "CLIStyleBackgroundSettings | None" = None,
    live: "CLIStyleLiveSettings | int | None" = None,
) -> None:
    """
    Stylized print function built with `rich`. This method maintains
    all standard functionality of the print function, with no overhead
    unless the styled parameters are provided.

    Args:
        *values : The values to print.
        sep : The separator between values.
        end : The end character.
        file : The file to write to.
        flush : Whether to flush the file.
        style : A color or style name to apply to the content.
        style_settings : A dictionary of style settings to apply to the content.
        bg : A color or box name to apply to the background.
        bg_settings : A dictionary of background settings to apply to the content.
        live : A dictionary of live settings or an integer in seconds to run the print in a live renderable.

        NOTE: If `live` is set as an integer, transient is True.

    Returns:
        None

    Raises:
        PrintError : If the renderable is not a RenderableType.
    """

    # If no styling parameters are provided, use built-in print to avoid rich's default styling
    if (
        style is None
        and style_settings is None
        and bg is None
        and bg_settings is None
        and live is None
    ):
        builtins.print(*values, sep=sep, end=end, file=file, flush=flush)
        return

    # Convert values to string for styling
    content = sep.join(str(value) for value in values)

    # Apply styling and background
    live_render, style_renderable = _get_style_utils()
    styled_content = style_renderable(
        content,
        style=style,
        style_settings=style_settings,
        bg=bg,
        bg_settings=bg_settings,
    )

    # Handle live rendering
    if live is not None:
        if isinstance(live, int):
            # If live is an integer, treat it as duration in seconds
            from ..styles.settings import CLIStyleLiveSettings

            live_settings: CLIStyleLiveSettings = {
                "duration": float(live),
                "transient": False,  # Changed to False for testing
            }
        else:
            live_settings = live

        # For very short durations or testing, just print normally
        duration = live if isinstance(live, int) else live_settings.get("duration", 2.0)
        if duration <= 1:
            get_console = _get_rich_console()
            Console, _ = _get_rich_console_classes()
            console = get_console() if file is None else Console(file=file)
            console.print(styled_content, end=end)
        else:
            live_render(styled_content, live_settings)
    else:
        # Regular print with styling
        get_console = _get_rich_console()
        Console, _ = _get_rich_console_classes()
        console = get_console() if file is None else Console(file=file)
        console.print(styled_content, end=end)


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


def _collect_fields_sequentially(schema: Any, console) -> Dict[str, Any]:
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

                Prompt, _ = _get_rich_prompts()
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

                Prompt, _ = _get_rich_prompts()
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

                Prompt, _ = _get_rich_prompts()
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
                Prompt, _ = _get_rich_prompts()
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
    style: "CLIStyleType | None" = None,
    style_settings: "CLIStyleRenderableSettings | None" = None,
    bg: "CLIStyleBackgroundType | None" = None,
    bg_settings: "CLIStyleBackgroundSettings | None" = None,
    multiline: bool = False,
    password: bool = False,
    complete: Optional[List[str]] = None,
    validate: Optional[callable] = None,
) -> Any: ...


def input(
    prompt: str = "",
    schema: Any = None,
    sequential: bool = True,
    style: "CLIStyleType | None" = None,
    style_settings: "CLIStyleRenderableSettings | None" = None,
    bg: "CLIStyleBackgroundType | None" = None,
    bg_settings: "CLIStyleBackgroundSettings | None" = None,
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
    get_console = _get_rich_console()
    console = get_console()

    try:
        # If no special features are requested, use built-in input for compatibility
        if (
            schema is None
            and style is None
            and style_settings is None
            and bg is None
            and bg_settings is None
            and not multiline
            and not password
            and complete is None
            and validate is None
        ):
            return builtins.input(prompt)

        # Apply styling to prompt if provided
        _, style_renderable = _get_style_utils()
        styled_prompt = style_renderable(
            prompt,
            style=style,
            style_settings=style_settings,
            bg=bg,
            bg_settings=bg_settings,
        )

        # Handle schema-based input
        if schema is not None:
            # Handle bool schema with Confirm.ask
            if schema == bool:
                Prompt, Confirm = _get_rich_prompts()
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
        Prompt, Confirm = _get_rich_prompts()
        if password:
            value = Prompt.ask(styled_prompt, password=True)
        elif complete:
            # Use prompt_toolkit for completion
            pt_prompt, WordCompleter = _get_prompt_toolkit()
            completer = WordCompleter(complete)
            value = pt_prompt(str(styled_prompt), completer=completer)
        elif multiline:
            console.print(styled_prompt, end="")
            lines = []
            console.print("[dim](Enter empty line to finish)[/dim]")
            pt_prompt, _ = _get_prompt_toolkit()
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


@overload
def animate(
    renderable: "RenderableType",
    type: Literal["flashing"],
    duration: Optional[float] = None,
    speed: float = 0.5,
    colors: "Optional[List[CLIStyleColorName]]" = None,
) -> None: ...


@overload
def animate(
    renderable: "RenderableType",
    type: Literal["pulsing"],
    duration: Optional[float] = None,
    speed: float = 2.0,
    min_opacity: float = 0.3,
    max_opacity: float = 1.0,
    color: "CLIStyleColorName" = "white",
) -> None: ...


@overload
def animate(
    renderable: "RenderableType",
    type: Literal["shaking"],
    duration: Optional[float] = None,
    intensity: int = 1,
    speed: float = 0.1,
) -> None: ...


@overload
def animate(
    text: str,
    type: Literal["typing"],
    duration: Optional[float] = None,
    speed: float = 0.05,
) -> None: ...


@overload
def animate(
    renderable: "RenderableType",
    type: Literal["spinning"],
    duration: Optional[float] = None,
    frames: Optional[List[str]] = None,
    speed: float = 0.1,
    prefix: bool = True,
) -> None: ...


@overload
def animate(
    renderable: "RenderableType",
    type: Literal["rainbow"],
    duration: Optional[float] = None,
    speed: float = 0.5,
    colors: "RainbowPreset | List[CLIStyleColorName] | None" = None,
) -> None: ...


def animate(
    renderable: "RenderableType | str",
    type: Literal["flashing", "pulsing", "shaking", "typing", "spinning", "rainbow"],
    duration: Optional[float] = None,
    **kwargs,
) -> None:
    """Create and run an animation based on the specified type.

    Args:
        type: The type of animation to create
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        **kwargs: Additional parameters specific to each animation type

    Examples:
        >>> animate("flashing", "Alert!", duration=3.0, speed=0.3)
        >>> animate("pulsing", Panel("Loading"), min_opacity=0.1)
        >>> animate("typing", "Hello World!", speed=0.1)
        >>> animate("rainbow", "Colorful!", colors="bright")
    """
    animations = _get_animation_classes()

    if type == "flashing":
        speed = kwargs.get("speed", 0.5)
        colors = kwargs.get("colors", None)
        animation = animations["CLIFlashingAnimation"](
            renderable, speed=speed, colors=colors, duration=duration
        )
    elif type == "pulsing":
        speed = kwargs.get("speed", 2.0)
        min_opacity = kwargs.get("min_opacity", 0.3)
        max_opacity = kwargs.get("max_opacity", 1.0)
        color = kwargs.get("color", "white")
        animation = animations["CLIPulsingAnimation"](
            renderable,
            speed=speed,
            min_opacity=min_opacity,
            max_opacity=max_opacity,
            color=color,
            duration=duration,
        )
    elif type == "shaking":
        intensity = kwargs.get("intensity", 1)
        speed = kwargs.get("speed", 0.1)
        animation = animations["CLIShakingAnimation"](
            renderable, intensity=intensity, speed=speed, duration=duration
        )
    elif type == "typing":
        speed = kwargs.get("speed", 0.05)
        animation = animations["CLITypingAnimation"](
            renderable, speed=speed, duration=duration
        )
    elif type == "spinning":
        frames = kwargs.get("frames", None)
        speed = kwargs.get("speed", 0.1)
        prefix = kwargs.get("prefix", True)
        animation = animations["CLISpinningAnimation"](
            renderable, frames=frames, speed=speed, prefix=prefix, duration=duration
        )
    elif type == "rainbow":
        speed = kwargs.get("speed", 0.5)
        colors = kwargs.get("colors", None)
        animation = animations["CLIRainbowAnimation"](
            renderable, speed=speed, colors=colors, duration=duration
        )
    else:
        raise ValueError(f"Unknown animation type: {type}")

    animation.animate()


__all__ = ("print", "input", "animate")
