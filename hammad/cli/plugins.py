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
    from rich.console import (
        JustifyMethod,
        OverflowMethod,
        Console,
        RenderableType,
    )
    from rich.panel import PaddingDimensions
    from rich.prompt import Prompt, Confirm
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter
    from .animations import (
        CLIFlashingAnimation,
        CLIPulsingAnimation,
        CLIShakingAnimation,
        CLITypingAnimation,
        CLISpinningAnimation,
        CLIRainbowAnimation,
        RainbowPreset,
    )
    from .styles.types import (
        CLIStyleType,
        CLIStyleBackgroundType,
        CLIStyleColorName,
        CLIStyleBoxName,
    )
    from .styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )
    from .styles.utils import (
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
        from .styles.utils import live_render, style_renderable

        _IMPORT_CACHE["style_utils"] = (live_render, style_renderable)
    return _IMPORT_CACHE["style_utils"]


def _get_animation_classes():
    """Lazy import for animation classes"""
    if "animations" not in _IMPORT_CACHE:
        from .animations import (
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
    justify: Optional["JustifyMethod"] = None,
    overflow: Optional["OverflowMethod"] = None,
    no_wrap: Optional[bool] = None,
    emoji: Optional[bool] = None,
    markup: Optional[bool] = None,
    highlight: Optional[bool] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    border: Optional["CLIStyleBoxName"] = None,
    padding: Optional["PaddingDimensions"] = None,
    title: Optional[str] = None,
    expand: Optional[bool] = None,
    live: "CLIStyleLiveSettings | int | None" = None,
    duration: Optional[float] = None,
    transient: bool = False,
    new_line_start: bool = False,
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
        justify : Text justification method ("left", "center", "right", "full").
        overflow : Text overflow method ("fold", "crop", "ellipsis", "ignore").
        no_wrap : Disable text wrapping.
        emoji : Enable/disable emoji rendering.
        markup : Enable/disable Rich markup rendering.
        highlight : Enable/disable automatic highlighting.
        width : Override the width of the output.
        height : Override the height of the output.
        border : Border style for panel rendering.
        padding : Padding dimensions for panel rendering.
        title : Title for panel rendering.
        expand : Whether to expand panel to full width.
        live : A dictionary of live settings or an integer in seconds to run the print in a live renderable.
        duration : The duration of the live renderable.
        transient : Whether to clear the output after completion.
        new_line_start : Start with a new line before printing.

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
        and justify is None
        and overflow is None
        and no_wrap is None
        and emoji is None
        and markup is None
        and highlight is None
        and width is None
        and height is None
        and border is None
        and padding is None
        and title is None
        and expand is None
        and not transient
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
        border=border,
        padding=padding,
        title=title,
        expand=expand,
    )

    # Handle live rendering
    if live is not None:
        if isinstance(live, int):
            # If live is an integer, treat it as duration in seconds
            from .styles.settings import CLIStyleLiveSettings

            live_settings: CLIStyleLiveSettings = {
                "duration": float(live),
                "transient": transient,  # Use the transient parameter
            }
        else:
            live_settings = live

        # For very short durations or testing, just print normally
        duration = live if isinstance(live, int) else live_settings.get("duration", 2.0)
        if duration <= 1:
            get_console = _get_rich_console()
            Console, _ = _get_rich_console_classes()
            console = get_console() if file is None else Console(file=file)
            console.print(
                styled_content,
                end=end,
                justify=justify,
                overflow=overflow,
                no_wrap=no_wrap,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
                width=width,
                height=height,
                new_line_start=new_line_start,
            )
        else:
            live_render(styled_content, live_settings)
    else:
        # Regular print with styling
        get_console = _get_rich_console()
        Console, _ = _get_rich_console_classes()
        console = get_console() if file is None else Console(file=file)

        if transient:
            # Use Rich's Live with transient for temporary output
            import time
            from rich.live import Live

            # Auto-set duration to 2.5 when transient=True and duration is None
            display_duration = duration if duration is not None else 2.5

            with Live(
                styled_content,
                console=console,
                refresh_per_second=1,
                transient=True,
                auto_refresh=False,
            ) as live:
                live.update(styled_content)
                live.refresh()
                time.sleep(
                    display_duration
                )  # Use duration parameter for transient content
        else:
            console.print(
                styled_content,
                end=end,
                justify=justify,
                overflow=overflow,
                no_wrap=no_wrap,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
                width=width,
                height=height,
                new_line_start=new_line_start,
            )


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
            from ..typing import get_type_description
            import dataclasses

            fields_info = schema.__dataclass_fields__
            console.print(
                f"\n[bold blue]Entering data for {schema.__name__}:[/bold blue]"
            )

            for field_name, field_info in fields_info.items():
                field_type = field_info.type
                default = getattr(field_info, "default", None)

                prompt_text = f"  {field_name}"
                if default is not None and default is not dataclasses.MISSING:
                    prompt_text += f" (default: {default})"
                elif hasattr(field_type, "__name__"):
                    prompt_text += f" ({field_type.__name__})"
                else:
                    prompt_text += f" ({get_type_description(field_type)})"
                prompt_text += ""

                Prompt, _ = _get_rich_prompts()
                value = Prompt.ask(prompt_text)
                if (
                    not value
                    and default is not None
                    and default is not dataclasses.MISSING
                ):
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


def animate(
    renderable: "RenderableType | str",
    type: Literal[
        "flashing", "pulsing", "shaking", "typing", "spinning", "rainbow"
    ] = "pulsing",
    duration: Optional[float] = None,
    # Animation parameters (defaults are handled by the specific animation classes)
    speed: Optional[float] = None,
    colors: "Optional[List[CLIStyleColorName]]" = None,
    on_color: "Optional[CLIStyleColorName]" = None,
    off_color: "Optional[CLIStyleColorName]" = None,
    min_opacity: Optional[float] = None,
    max_opacity: Optional[float] = None,
    color: "Optional[CLIStyleColorName]" = None,
    intensity: Optional[int] = None,
    typing_speed: Optional[float] = None,
    cursor: Optional[str] = None,
    show_cursor: Optional[bool] = None,
    frames: Optional[List[str]] = None,
    prefix: Optional[bool] = None,
    # Rich.Live parameters
    refresh_rate: int = 20,
    transient: bool = True,
    auto_refresh: bool = True,
    console: Optional["Console"] = None,
    screen: bool = False,
    vertical_overflow: str = "ellipsis",
) -> None:
    """Create and run an animation based on the specified type.

    Args:
        renderable: The object to animate (text, panel, etc.)
        type: The type of animation to create
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Animation speed (defaults to the specific animation class's default)
        colors: Color list (used by flashing, rainbow) (defaults to the specific animation class's default)
        on_color: Color when flashing "on" (used by flashing) (defaults to the specific animation class's default)
        off_color: Color when flashing "off" (used by flashing) (defaults to the specific animation class's default)
        min_opacity: Minimum opacity for pulsing animation (defaults to the specific animation class's default)
        max_opacity: Maximum opacity for pulsing animation (defaults to the specific animation class's default)
        color: Color for pulsing animation (defaults to the specific animation class's default)
        intensity: Shaking intensity for shaking animation (defaults to the specific animation class's default)
        typing_speed: Speed for typing animation (used by typing) (defaults to the specific animation class's default)
        cursor: Cursor character for typing animation (used by typing) (defaults to the specific animation class's default)
        show_cursor: Whether to show cursor for typing animation (used by typing) (defaults to the specific animation class's default)
        frames: Custom frames for spinning animation (defaults to the specific animation class's default)
        prefix: Whether to show spinner as prefix for spinning animation (defaults to the specific animation class's default)
        refresh_rate: Refresh rate per second for Live rendering
        transient: Whether to clear animation after completion
        auto_refresh: Whether to auto-refresh the display
        console: Console to use for rendering
        screen: Whether to use alternate screen buffer
        vertical_overflow: How to handle vertical overflow

    Examples:
        >>> animate("Hello!", type="flashing", duration=3.0, speed=0.3)
        >>> animate(Panel("Loading"), type="pulsing", min_opacity=0.1)
        >>> animate("Hello World!", type="typing", typing_speed=0.1)
        >>> animate("Colorful!", type="rainbow", colors=["red", "blue"])
    """
    animations = _get_animation_classes()

    if type == "flashing":
        animation = animations["CLIFlashingAnimation"](
            renderable,
            speed=speed if speed is not None else 0.5,
            colors=colors,  # Class handles default if None
            on_color=on_color if on_color is not None else "white",
            off_color=off_color if off_color is not None else "dim white",
            duration=duration,  # Base class handles default if None
        )
    elif type == "pulsing":
        animation = animations["CLIPulsingAnimation"](
            renderable,
            speed=speed if speed is not None else 2.0,
            min_opacity=min_opacity if min_opacity is not None else 0.3,
            max_opacity=max_opacity if max_opacity is not None else 1.0,
            color=color if color is not None else "white",
            duration=duration,  # Base class handles default if None
        )
    elif type == "shaking":
        animation = animations["CLIShakingAnimation"](
            renderable,
            intensity=intensity if intensity is not None else 1,
            speed=speed if speed is not None else 0.1,
            duration=duration,  # Base class handles default if None
        )
    elif type == "typing":
        # Note: CLITypingAnimation expects 'text', assuming renderable is a string here.
        animation = animations[
            "CLITypingAnimation"
        ](
            renderable,
            speed=speed
            if speed is not None
            else 0.05,  # Pass animate's speed, using CLITypingAnimation's speed default
            typing_speed=typing_speed,  # Pass animate's typing_speed, CLITypingAnimation handles its None default
            cursor=cursor if cursor is not None else "█",
            show_cursor=show_cursor if show_cursor is not None else True,
            duration=duration,  # Base class handles default if None
        )
    elif type == "spinning":
        animation = animations["CLISpinningAnimation"](
            renderable,
            frames=frames,  # Class handles default if None
            speed=speed if speed is not None else 0.1,
            prefix=prefix if prefix is not None else True,
            duration=duration,  # Base class handles default if None
        )
    elif type == "rainbow":
        animation = animations["CLIRainbowAnimation"](
            renderable,
            speed=speed if speed is not None else 0.5,
            colors=colors,  # Class handles default if None
            duration=duration,  # Base class handles default if None
        )
    else:
        raise ValueError(f"Unknown animation type: {type}")

    # The animation object's animate method handles its own duration default
    # and the Live parameters are passed directly from the function args
    animation.animate(
        duration=duration,
        refresh_rate=refresh_rate,
        transient=transient,
        auto_refresh=auto_refresh,
        console=console,
        screen=screen,
        vertical_overflow=vertical_overflow,
    )


__all__ = ("print", "input", "animate")
