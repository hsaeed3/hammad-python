"""hammad.cli._runner"""

from typing import (
    overload,
    TYPE_CHECKING,
    Optional,
    Any,
    Dict,
    List,
    Union,
    Literal,
    IO,
)

if TYPE_CHECKING:
    from rich.console import Console, RenderableType
    from ..cli.animations import (
        CLIFlashingAnimation,
        CLIPulsingAnimation,
        CLIShakingAnimation,
        CLITypingAnimation,
        CLISpinningAnimation,
        CLIRainbowAnimation,
        RainbowPreset,
    )
    from ..cli.styles.types import (
        CLIStyleType,
        CLIStyleBackgroundType,
        CLIStyleColorName,
    )
    from ..cli.styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )


__all__ = ("CLIRunner",)


class CLIRunner:
    """Runner subclass for various CLI-based operations."""

    @overload
    @staticmethod
    def print(
        *values: object,
        sep: str = " ",
        end: str = "\n",
        file: Optional[IO[str]] = None,
        flush: bool = False,
    ) -> None: ...

    @overload
    @staticmethod
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

    @staticmethod
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
    ) -> Optional["CLIStyleLiveSettings"]:
        """Print values to the console with optional styling and live updates.

        This function extends Python's built-in print() with additional styling
        capabilities including backgrounds and live updating displays.

        Args:
            *values: Values to print (similar to built-in print())
            sep: String inserted between values (default: " ")
            end: String appended after the last value (default: "\n")
            file: File object to write to (default: sys.stdout)
            flush: Whether to forcibly flush the stream
            console: Rich Console instance to use
            style: Style to apply to the content
            color: Color to apply to the content
            bg: Background style to apply
            live: Whether to enable live updating
            live_settings: Configuration for live display
            settings: General rendering settings
            bg_settings: Background styling settings
            **kwargs: Additional keyword arguments

        Returns:
            Live settings object if live=True, otherwise None
        """
        from ..cli import print as _run_cli_print_fn

        return _run_cli_print_fn(
            *values,
            sep=sep,
            end=end,
            file=file,
            flush=flush,
            style=style,
            style_settings=style_settings,
            bg=bg,
            bg_settings=bg_settings,
            live=live,
        )

    @overload
    @staticmethod
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

    @staticmethod
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
        """Get input from the user with optional validation and styling.

        Args:
            prompt: The prompt message to display.
            schema: Optional schema (dataclass, TypedDict, Pydantic model) for structured input.
            sequential: If schema is provided, collect fields sequentially (default: True).
            style: A color or style name to apply to the prompt.
            style_settings: A dictionary of style settings to apply to the prompt.
            bg: A color or box name to apply to the background of the prompt.
            bg_settings: A dictionary of background settings to apply to the prompt.
            multiline: Allow multiline input (default: False).
            password: Hide input (default: False).
            complete: List of strings for autocompletion.
            validate: A callable to validate the input.

        Returns:
            The user's input, potentially validated and converted according to the schema.
        """
        from ..cli import input as _run_cli_input_fn

        return _run_cli_input_fn(
            prompt=prompt,
            schema=schema,
            sequential=sequential,
            style=style,
            style_settings=style_settings,
            bg=bg,
            bg_settings=bg_settings,
            multiline=multiline,
            password=password,
            complete=complete,
            validate=validate,
        )

    @staticmethod
    def animate(
        renderable: "RenderableType | str",
        type: Literal[
            "flashing", "pulsing", "shaking", "typing", "spinning", "rainbow"
        ],
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
            speed: Animation speed (used by flashing, pulsing, shaking, spinning, rainbow)
            colors: Color list (used by flashing, rainbow)
            on_color: Color when flashing "on" (used by flashing)
            off_color: Color when flashing "off" (used by flashing)
            min_opacity: Minimum opacity for pulsing animation
            max_opacity: Maximum opacity for pulsing animation
            color: Color for pulsing animation
            intensity: Shaking intensity for shaking animation
            typing_speed: Speed for typing animation (used by typing)
            cursor: Cursor character for typing animation (used by typing)
            show_cursor: Whether to show cursor for typing animation (used by typing)
            frames: Custom frames for spinning animation
            prefix: Whether to show spinner as prefix for spinning animation
            refresh_rate: Refresh rate per second for Live rendering
            transient: Whether to clear animation after completion
            auto_refresh: Whether to auto-refresh the display
            console: Console to use for rendering
            screen: Whether to use alternate screen buffer
            vertical_overflow: How to handle vertical overflow
        """
        from ..cli import animate as _run_cli_animate_fn

        _run_cli_animate_fn(
            renderable=renderable,
            type=type,
            duration=duration,
            speed=speed,
            colors=colors,
            on_color=on_color,
            off_color=off_color,
            min_opacity=min_opacity,
            max_opacity=max_opacity,
            color=color,
            intensity=intensity,
            typing_speed=typing_speed,
            cursor=cursor,
            show_cursor=show_cursor,
            frames=frames,
            prefix=prefix,
            refresh_rate=refresh_rate,
            transient=transient,
            auto_refresh=auto_refresh,
            console=console,
            screen=screen,
            vertical_overflow=vertical_overflow,
        )
