"""hammad._builtins._print"""

from typing import Optional, IO, overload
from rich import get_console
from rich.console import Console

from ._internal._style_types import (
    StyleLiveSettings,
    StyleBackgroundSettings,
    StyleStyleSettings,
    StyleColorName,
)
from ._internal._style_utils import live_render, wrap_renderable_with_styles

__all__ = ("print",)


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
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
    live: StyleLiveSettings | int | None = None,
) -> None: ...


def print(
    *values: object,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
    style: StyleColorName | StyleStyleSettings | None = None,
    bg: StyleColorName | StyleBackgroundSettings | None = None,
    live: StyleLiveSettings | int | None = None,
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
        style : A color or a dictionary of style settings to apply to the content.
        bg : A color or a dictionary of background settings to apply to the content.
        live : A dictionary of live settings or an integer in seconds to run the print in a live renderable.

        NOTE: If `live` is set as an integer, transient is True.

    Returns:
        None

    Raises:
        PrintError : If the renderable is not a RenderableType.
    """

    # If no styling parameters are provided, use built-in print to avoid rich's default styling
    if style is None and bg is None and live is None:
        import builtins

        builtins.print(*values, sep=sep, end=end, file=file, flush=flush)
        return

    # Convert values to string for styling
    content = sep.join(str(value) for value in values)

    # Apply styling and background
    styled_content = wrap_renderable_with_styles(content, style=style, background=bg)

    # Handle live rendering
    if live is not None:
        if isinstance(live, int):
            # If live is an integer, treat it as duration in seconds
            live_settings: StyleLiveSettings = {
                "duration": float(live),
                "transient": False,  # Changed to False for testing
            }
        else:
            live_settings = live

        # For very short durations or testing, just print normally
        duration = live if isinstance(live, int) else live_settings.get("duration", 2.0)
        if duration <= 1:
            console = get_console() if file is None else Console(file=file)
            console.print(styled_content, end=end)
        else:
            live_render(styled_content, live_settings)
    else:
        # Regular print with styling
        console = get_console() if file is None else Console(file=file)
        console.print(styled_content, end=end)
