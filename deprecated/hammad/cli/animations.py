"""hammad.cli.animations"""

import time
import math
import random
import threading
from dataclasses import dataclass, field
from typing import Literal, Optional, List, overload, TYPE_CHECKING

from rich import get_console
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

from .styles.types import (
    CLIStyleColorName,
)


__all__ = (
    "CLIAnimation",
    "CLIAnimationState",
    "CLIFlashingAnimation",
    "CLIPulsingAnimation",
    "CLIShakingAnimation",
    "CLITypingAnimation",
    "CLISpinningAnimation",
    "CLIRainbowAnimation",
    "animate_flashing",
    "animate_pulsing",
    "animate_shaking",
    "animate_spinning",
    "animate_rainbow",
    "animate_typing",
)


@dataclass
class CLIAnimationState:
    """Internal class used to track the current state of an
    animation."""

    start_time: float = field(default_factory=time.time)
    frame: int = 0
    last_update: float | None = field(default_factory=time.time)


@dataclass
class CLIAnimation:
    """Base class for all animations within the `hammad` package,
    this is used to integrate with rich's `__rich_console__` protocol."""

    def __init__(
        self,
        # The object that this animation is being applied to.
        renderable,
        duration: Optional[float] = None,
    ) -> None:
        self.renderable = renderable
        """The object that this animation is being applied to."""
        self.duration = duration or 2.0
        """The duration of the animation in seconds (defaults to 2.0 seconds)."""
        # Set last_update to None to ensure the animation is classified as
        # the first update on init.
        self.state = CLIAnimationState(last_update=None)
        """The current state of the animation."""

        self.rich_console = get_console()
        """The rich console responsible for rendering the animation."""
        self._animation_thread: threading.Thread | None = None
        """The thread responsible for running the animation."""
        self._stop_animation = False
        """Flag used to stop the animation."""

    def __rich_console__(
        self,
        console,
        options,
    ):
        """Rich will call this automatically when rendering."""
        if not self.is_complete:
            console.force_terminal = True
            if console.is_terminal:
                # force referesh
                console._is_alt_screen = False

        current_time = time.time()
        self.state.frame += 1
        self.state.last_update = current_time

        yield from self.apply(console, options)

    def apply(self, console, options):
        """Used by subclasses to apply the animation."""
        yield self.renderable

    @property
    def time_elapsed(self) -> float:
        """Time elapsed since the animation started."""
        return time.time() - self.state.start_time

    @property
    def is_complete(self) -> bool:
        """Check if the animation is complete."""
        if self.duration is None:
            return False
        return self.time_elapsed >= self.duration

    def animate(
        self,
        duration: Optional[float] = None,
        refresh_rate: int = 20,
        transient: bool = True,
        auto_refresh: bool = True,
        console: Optional["Console"] = None,
        screen: bool = False,
        vertical_overflow: str = "ellipsis",
    ) -> None:
        """Animate this effect for the specified duration using Live."""
        animate_duration = duration or self.duration or 3.0

        # Use provided console or create new one
        live_console = console or get_console()

        with Live(
            self,
            console=live_console,
            refresh_per_second=refresh_rate,
            transient=transient,
            auto_refresh=auto_refresh,
            screen=screen,
            vertical_overflow=vertical_overflow,
        ) as live:
            start = time.time()
            while time.time() - start < animate_duration:
                time.sleep(0.05)


class CLIFlashingAnimation(CLIAnimation):
    """Makes any renderable flash/blink."""

    def __init__(
        self,
        renderable,
        speed: float = 0.5,
        colors: Optional[List[CLIStyleColorName]] = None,
        on_color: CLIStyleColorName = "white",
        off_color: CLIStyleColorName = "dim white",
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed
        # If colors is provided, use it; otherwise use on_color/off_color
        if colors is not None:
            self.colors = colors
        else:
            self.colors = [on_color, off_color]

    def apply(self, console, options):
        # Calculate which color to use based on time
        color_index = int(self.time_elapsed / self.speed) % len(self.colors)
        color = self.colors[color_index]

        # Apply color to the renderable
        if isinstance(self.renderable, str):
            yield Text(self.renderable, style=color)
        else:
            # Wrap any renderable in the flash color
            yield Text.from_markup(f"[{color}]{self.renderable}[/{color}]")


class CLIPulsingAnimation(CLIAnimation):
    """Makes any renderable pulse/breathe."""

    def __init__(
        self,
        renderable: "RenderableType",
        speed: float = 2.0,
        min_opacity: float = 0.3,
        max_opacity: float = 1.0,
        color: "CLIStyleColorName" = "white",
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed
        self.min_opacity = min_opacity
        self.max_opacity = max_opacity
        self.color = color

    def apply(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        # Calculate opacity using sine wave
        opacity = self.min_opacity + (self.max_opacity - self.min_opacity) * (
            0.5 + 0.5 * math.sin(self.time_elapsed * self.speed)
        )

        # Convert opacity to RGB values for fading effect
        rgb_value = int(opacity * 255)
        fade_color = f"rgb({rgb_value},{rgb_value},{rgb_value})"

        if isinstance(self.renderable, str):
            yield Text(self.renderable, style=fade_color)
        else:
            # For Panel and other renderables, we need to use opacity styling
            if isinstance(self.renderable, Panel):
                # Create a new panel with modified style
                new_panel = Panel(
                    self.renderable.renderable,
                    title=self.renderable.title,
                    title_align=self.renderable.title_align,
                    subtitle=self.renderable.subtitle,
                    subtitle_align=self.renderable.subtitle_align,
                    box=self.renderable.box,
                    style=fade_color,
                    border_style=fade_color,
                    expand=self.renderable.expand,
                    padding=self.renderable.padding,
                    width=self.renderable.width,
                    height=self.renderable.height,
                )
                yield new_panel
            else:
                # For other renderables, wrap in a panel with the fade effect
                yield Panel(self.renderable, style=fade_color, border_style=fade_color)


class CLIShakingAnimation(CLIAnimation):
    """Makes text shake/jitter."""

    def __init__(
        self,
        renderable: "RenderableType",
        intensity: int = 1,
        speed: float = 0.1,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.intensity = intensity
        self.speed = speed
        self.last_shake = 0

    def apply(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        if self.time_elapsed - self.last_shake > self.speed:
            self.last_shake = self.time_elapsed

            # Add random spaces for shake effect
            shake = " " * random.randint(0, self.intensity)

            if isinstance(self.renderable, str):
                yield Text(shake + self.renderable)
            else:
                yield Text(shake) + self.renderable
        else:
            # Keep previous position
            yield self.renderable


class CLITypingAnimation(CLIAnimation):
    """Typewriter effect."""

    def __init__(
        self,
        text: str,
        speed: float = 0.05,
        typing_speed: Optional[float] = None,
        cursor: str = "█",
        show_cursor: bool = True,
        duration: Optional[float] = None,
    ):
        super().__init__(text, duration)
        self.text = text
        # Use typing_speed if provided, otherwise use speed
        self.speed = typing_speed if typing_speed is not None else speed
        self.cursor = cursor
        self.show_cursor = show_cursor

    def apply(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        # Calculate how many characters to show
        chars_to_show = int(self.time_elapsed / self.speed)
        chars_to_show = min(chars_to_show, len(self.text))

        if chars_to_show < len(self.text):
            # Still typing - show cursor if enabled
            text_content = self.text[:chars_to_show]
            if self.show_cursor:
                text_content += self.cursor
            yield Text(text_content)
        else:
            # Finished typing - show complete text without cursor
            yield Text(self.text)


class CLISpinningAnimation(CLIAnimation):
    """Spinner effect for any renderable."""

    def __init__(
        self,
        renderable: "RenderableType",
        frames: Optional[List[str]] = None,
        speed: float = 0.1,
        prefix: bool = True,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.frames = frames or ["⋅", "•", "●", "◉", "●", "•"]
        self.speed = speed
        self.prefix = prefix

    def apply(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        frame_index = int(self.time_elapsed / self.speed) % len(self.frames)
        spinner = self.frames[frame_index]

        if isinstance(self.renderable, str):
            if self.prefix:
                yield Text(f"{spinner} {self.renderable}")
            else:
                yield Text(f"{self.renderable} {spinner}")
        else:
            if self.prefix:
                yield Text(f"{spinner} ") + self.renderable
            else:
                yield self.renderable + Text(f" {spinner}")


RainbowPreset = Literal["classic", "bright", "pastel", "neon"]

RAINBOW_PRESETS = {
    "classic": ["red", "yellow", "green", "cyan", "blue", "magenta"],
    "bright": [
        "bright_red",
        "bright_yellow",
        "bright_green",
        "bright_cyan",
        "bright_blue",
        "bright_magenta",
    ],
    "pastel": [
        "light_pink3",
        "khaki1",
        "light_green",
        "light_cyan1",
        "light_blue",
        "plum2",
    ],
    "neon": ["hot_pink", "yellow1", "green1", "cyan1", "blue1", "magenta1"],
}


class CLIRainbowAnimation(CLIAnimation):
    """Rainbow color cycling effect."""

    def __init__(
        self,
        renderable: "RenderableType",
        speed: float = 0.5,
        colors: "RainbowPreset | List[CLIStyleColorName] | None" = None,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed

        # Handle color selection
        if colors is None:
            colors = "classic"

        if isinstance(colors, str) and colors in RAINBOW_PRESETS:
            self.colors = RAINBOW_PRESETS[colors]
        elif isinstance(colors, list):
            self.colors = colors
        else:
            self.colors = RAINBOW_PRESETS["classic"]

    def apply(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        if isinstance(self.renderable, str):
            # Apply rainbow to each character
            result = Text()
            for i, char in enumerate(self.renderable):
                color_offset = int(
                    (self.time_elapsed / self.speed + i) % len(self.colors)
                )
                color = self.colors[color_offset]
                result.append(char, style=color)
            yield result
        else:
            # Cycle through colors for the whole renderable
            color_index = int(self.time_elapsed / self.speed) % len(self.colors)
            yield Text.from_markup(
                f"[{self.colors[color_index]}]{self.renderable}[/{self.colors[color_index]}]"
            )


def animate_flashing(
    renderable: "RenderableType",
    duration: Optional[float] = None,
    speed: float = 0.5,
    on_color: CLIStyleColorName = "white",
    off_color: CLIStyleColorName = "dim white",
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a flashing animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the flashing effect (defaults to 0.5)
        on_color: Color when flashing "on" (defaults to "white")
        off_color: Color when flashing "off" (defaults to "dim white")
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_flashing("Alert!", duration=3.0, speed=0.3)
        >>> animate_flashing(Panel("Warning"), on_color="red", off_color="dark_red")
    """
    animation = CLIFlashingAnimation(
        renderable,
        duration=duration,
        speed=speed,
        on_color=on_color,
        off_color=off_color,
    )
    animation.animate(duration=duration, refresh_rate=refresh_rate)


def animate_pulsing(
    renderable: "RenderableType",
    duration: Optional[float] = None,
    speed: float = 1.0,
    min_opacity: float = 0.3,
    max_opacity: float = 1.0,
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a pulsing animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the pulsing effect (defaults to 1.0)
        min_opacity: Minimum opacity during pulse (defaults to 0.3)
        max_opacity: Maximum opacity during pulse (defaults to 1.0)
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_pulsing("Loading...", duration=5.0, speed=2.0)
        >>> animate_pulsing(Panel("Status"), min_opacity=0.1, max_opacity=0.9)
    """
    animation = CLIPulsingAnimation(
        renderable,
        duration=duration,
        speed=speed,
        min_opacity=min_opacity,
        max_opacity=max_opacity,
    )
    animation.animate(duration=duration, refresh_rate=refresh_rate)


def animate_shaking(
    renderable: "RenderableType",
    duration: Optional[float] = None,
    intensity: int = 2,
    speed: float = 10.0,
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a shaking animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        intensity: Intensity of the shake effect (defaults to 2)
        speed: Speed of the shaking motion (defaults to 10.0)
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_shaking("Error!", duration=1.5, intensity=3)
        >>> animate_shaking(Panel("Critical Alert"), speed=15.0)
    """
    animation = CLIShakingAnimation(
        renderable, duration=duration, intensity=intensity, speed=speed
    )
    animation.animate(duration=duration, refresh_rate=refresh_rate)


def animate_spinning(
    renderable: "RenderableType",
    duration: Optional[float] = None,
    frames: Optional[List[str]] = None,
    speed: float = 0.1,
    prefix: bool = True,
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a spinning animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        frames: List of spinner frames (defaults to ["⋅", "•", "●", "◉", "●", "•"])
        speed: Speed between frame changes (defaults to 0.1)
        prefix: Whether to show spinner before text (defaults to True)
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_spinning("Processing...", duration=10.0, speed=0.2)
        >>> animate_spinning("Done", frames=["◐", "◓", "◑", "◒"], prefix=False)
    """
    animation = CLISpinningAnimation(
        renderable, duration=duration, frames=frames, speed=speed, prefix=prefix
    )
    animation.animate(duration=duration, refresh_rate=refresh_rate)


def animate_rainbow(
    renderable: "RenderableType",
    duration: Optional[float] = None,
    speed: float = 0.5,
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a rainbow animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the color cycling effect (defaults to 0.5)
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_rainbow("Colorful Text!", duration=4.0, speed=1.0)
        >>> animate_rainbow(Panel("Rainbow Panel"), speed=0.3)
    """
    animation = CLIRainbowAnimation(renderable, duration=duration, speed=speed)
    animation.animate(duration=duration, refresh_rate=refresh_rate)


def animate_typing(
    text: str,
    duration: Optional[float] = None,
    typing_speed: float = 0.05,
    cursor: str = "▌",
    show_cursor: bool = True,
    refresh_rate: int = 20,
    transient: bool = True,
) -> None:
    """Create and run a typewriter animation.

    Args:
        text: The text to type out
        duration: Duration of the animation in seconds (defaults to 2.0)
        typing_speed: Speed between character reveals (defaults to 0.05)
        cursor: Cursor character to show (defaults to "▌")
        show_cursor: Whether to show the typing cursor (defaults to True)
        refresh_rate: Refresh rate per second (defaults to 20)
        transient: Whether to clear animation after completion (defaults to True)

    Examples:
        >>> animate_typing("Hello, World!", typing_speed=0.1)
        >>> animate_typing("Fast typing", duration=1.0, cursor="|", show_cursor=False)
    """
    animation = CLITypingAnimation(
        text,
        duration=duration,
        typing_speed=typing_speed,
        cursor=cursor,
        show_cursor=show_cursor,
    )
    animation.animate(duration=duration, refresh_rate=refresh_rate)
