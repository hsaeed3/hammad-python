"""hammad.cli.animation

Contains resources that allow for easy animation through the `rich` library."""

from dataclasses import dataclass, field

from rich import get_console as _get_console
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.text import Text
from rich.live import Live
from rich.style import Style
from rich.panel import Panel
from typing import Optional, List
import time
import math
import random
import threading

from ._rich._types import RichColorName as _RichColorName


@dataclass
class AnimationState:
    """Internal class used to track the current state of an
    animation."""

    start_time: float = field(default_factory=time.time)
    frame: int = 0
    last_update: float | None = field(default_factory=time.time)


@dataclass
class Animation:
    """Base class for all animations within the `hammad` package,
    this is used to integrate with rich's `__rich_console__` protocol."""

    def __init__(
        self,
        # The object that this animation is being applied to.
        renderable: RenderableType,
        duration: Optional[float] = None,
    ) -> None:
        self.renderable = renderable
        """The object that this animation is being applied to."""
        self.duration = duration or 2.0
        """The duration of the animation in seconds (defaults to 2.0 seconds)."""
        # Set last_update to None to ensure the animation is classified as
        # the first update on init.
        self.state = AnimationState(last_update=None)
        """The current state of the animation."""

        self.rich_console = _get_console()
        """The rich console responsible for rendering the animation."""
        self._animation_thread: threading.Thread | None = None
        """The thread responsible for running the animation."""
        self._stop_animation = False
        """Flag used to stop the animation."""

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
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

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
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
    ) -> None:
        """Animate this effect for the specified duration using Live."""
        animate_duration = duration or self.duration or 3.0
        console = Console()

        with Live(
            self, console=console, refresh_per_second=refresh_rate, transient=True
        ) as live:
            start = time.time()
            while time.time() - start < animate_duration:
                time.sleep(0.05)


class Flashing(Animation):
    """Makes any renderable flash/blink."""

    def __init__(
        self,
        renderable: RenderableType,
        speed: float = 0.5,
        on_color: _RichColorName = "white",
        off_color: _RichColorName = "dim white",
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed
        self.on_color = on_color
        self.off_color = off_color

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Alternate between on_color and off_color based on time
        flash_cycle = int(self.time_elapsed / self.speed) % 2
        color = self.on_color if flash_cycle == 0 else self.off_color

        # Apply color to the renderable
        if isinstance(self.renderable, str):
            yield Text(self.renderable, style=color)
        else:
            # Wrap any renderable in the flash color
            yield Text.from_markup(f"[{color}]{self.renderable}[/{color}]")


class Pulsing(Animation):
    """Makes any renderable pulse/breathe."""

    def __init__(
        self,
        renderable: RenderableType,
        speed: float = 2.0,
        min_opacity: float = 0.3,
        max_opacity: float = 1.0,
        color: _RichColorName = "white",
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed
        self.min_opacity = min_opacity
        self.max_opacity = max_opacity
        self.color = color

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
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


class Shaking(Animation):
    """Makes text shake/jitter."""

    def __init__(
        self,
        renderable: RenderableType,
        intensity: int = 1,
        speed: float = 0.1,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.intensity = intensity
        self.speed = speed
        self.last_shake = 0

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
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


class Typing(Animation):
    """Typewriter effect."""

    def __init__(
        self,
        text: str,
        typing_speed: float = 0.05,
        cursor: str = "▌",
        show_cursor: bool = True,
        duration: Optional[float] = None,
    ):
        super().__init__(text, duration)
        self.text = text
        self.typing_speed = typing_speed
        self.cursor = cursor
        self.show_cursor = show_cursor

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Calculate how many characters to show
        chars_to_show = int(self.time_elapsed / self.typing_speed)
        chars_to_show = min(chars_to_show, len(self.text))

        if chars_to_show < len(self.text):
            # Still typing - show cursor if enabled
            display_text = self.text[:chars_to_show]
            if self.show_cursor:
                display_text += self.cursor
            yield Text(display_text)
        else:
            # Finished typing - show complete text without cursor
            yield Text(self.text)


class Spinning(Animation):
    """Spinner effect for any renderable."""

    def __init__(
        self,
        renderable: RenderableType,
        frames: Optional[List[str]] = None,
        speed: float = 0.1,
        prefix: bool = True,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.frames = frames or ["⋅", "•", "●", "◉", "●", "•"]
        self.speed = speed
        self.prefix = prefix

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
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


class Rainbow(Animation):
    """Rainbow color cycling effect."""

    def __init__(
        self,
        renderable: RenderableType,
        speed: float = 0.5,
        duration: Optional[float] = None,
    ):
        super().__init__(renderable, duration)
        self.speed = speed
        self.colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]

    def apply(self, console: Console, options: ConsoleOptions) -> RenderResult:
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
    renderable: RenderableType,
    duration: Optional[float] = None,
    speed: float = 0.5,
    on_color: _RichColorName = "white",
    off_color: _RichColorName = "dim white",
) -> None:
    """Create and run a flashing animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the flashing effect (defaults to 0.5)
        on_color: Color when flashing "on" (defaults to "white")
        off_color: Color when flashing "off" (defaults to "dim white")

    Examples:
        >>> animate_flashing("Alert!", duration=3.0, speed=0.3)
        >>> animate_flashing(Panel("Warning"), on_color="red", off_color="dark_red")
    """
    animation = Flashing(
        renderable,
        duration=duration,
        speed=speed,
        on_color=on_color,
        off_color=off_color,
    )
    animation.animate()


def animate_pulsing(
    renderable: RenderableType,
    duration: Optional[float] = None,
    speed: float = 1.0,
    min_opacity: float = 0.3,
    max_opacity: float = 1.0,
) -> None:
    """Create and run a pulsing animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the pulsing effect (defaults to 1.0)
        min_opacity: Minimum opacity during pulse (defaults to 0.3)
        max_opacity: Maximum opacity during pulse (defaults to 1.0)

    Examples:
        >>> animate_pulsing("Loading...", duration=5.0, speed=2.0)
        >>> animate_pulsing(Panel("Status"), min_opacity=0.1, max_opacity=0.9)
    """
    animation = Pulsing(
        renderable,
        duration=duration,
        speed=speed,
        min_opacity=min_opacity,
        max_opacity=max_opacity,
    )
    animation.animate()


def animate_shaking(
    renderable: RenderableType,
    duration: Optional[float] = None,
    intensity: int = 2,
    speed: float = 10.0,
) -> None:
    """Create and run a shaking animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        intensity: Intensity of the shake effect (defaults to 2)
        speed: Speed of the shaking motion (defaults to 10.0)

    Examples:
        >>> animate_shaking("Error!", duration=1.5, intensity=3)
        >>> animate_shaking(Panel("Critical Alert"), speed=15.0)
    """
    animation = Shaking(renderable, duration=duration, intensity=intensity, speed=speed)
    animation.animate()


def animate_spinning(
    renderable: RenderableType,
    duration: Optional[float] = None,
    frames: Optional[List[str]] = None,
    speed: float = 0.1,
    prefix: bool = True,
) -> None:
    """Create and run a spinning animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        frames: List of spinner frames (defaults to ["⋅", "•", "●", "◉", "●", "•"])
        speed: Speed between frame changes (defaults to 0.1)
        prefix: Whether to show spinner before text (defaults to True)

    Examples:
        >>> animate_spinning("Processing...", duration=10.0, speed=0.2)
        >>> animate_spinning("Done", frames=["◐", "◓", "◑", "◒"], prefix=False)
    """
    animation = Spinning(
        renderable, duration=duration, frames=frames, speed=speed, prefix=prefix
    )
    animation.animate()


def animate_rainbow(
    renderable: RenderableType, duration: Optional[float] = None, speed: float = 0.5
) -> None:
    """Create and run a rainbow animation on any renderable.

    Args:
        renderable: The object to animate (text, panel, etc.)
        duration: Duration of the animation in seconds (defaults to 2.0)
        speed: Speed of the color cycling effect (defaults to 0.5)

    Examples:
        >>> animate_rainbow("Colorful Text!", duration=4.0, speed=1.0)
        >>> animate_rainbow(Panel("Rainbow Panel"), speed=0.3)
    """
    animation = Rainbow(renderable, duration=duration, speed=speed)
    animation.animate()


def animate_typing(
    text: str,
    duration: Optional[float] = None,
    typing_speed: float = 0.05,
    cursor: str = "▌",
    show_cursor: bool = True,
) -> None:
    """Create and run a typewriter animation.

    Args:
        text: The text to type out
        duration: Duration of the animation in seconds (defaults to 2.0)
        typing_speed: Speed between character reveals (defaults to 0.05)
        cursor: Cursor character to show (defaults to "▌")
        show_cursor: Whether to show the typing cursor (defaults to True)

    Examples:
        >>> animate_typing("Hello, World!", typing_speed=0.1)
        >>> animate_typing("Fast typing", duration=1.0, cursor="|", show_cursor=False)
    """
    animation = Typing(
        text,
        duration=duration,
        typing_speed=typing_speed,
        cursor=cursor,
        show_cursor=show_cursor,
    )
    animation.animate()


if __name__ == "__main__":
    animate_flashing("Hello, world!")
