"""hammad.types.color"""

from dataclasses import dataclass
from typing import ClassVar
from rich.color import Color as _RichColorClass
from rich.text import Text
from rich.style import Style
from typing import Any, Dict, Optional, Tuple, TypeAlias, Union, Self

from ..cli._rich_types import (
    _COLORS_BY_NAME,
    _PYDANTIC_COLOR_NAMES,
    _RICH_COLOR_NAMES,
    _RichColorName,
    _PydanticColorName,
    _ALL_COLOR_NAMES,
)

__all__ = (
    "Color",
    "ColorName",
    "HexColor",
    "RGBColor",
)

# ------------------------------------------------------------
# Generic Color Types
# ------------------------------------------------------------

HexColor: TypeAlias = str
"""Hexadecimal color string."""

RGBColor: TypeAlias = Tuple[int, int, int]
"""RGB Color Tuple Parameter & Type."""

ColorName: TypeAlias = Union[_RichColorName, _PydanticColorName]
ColorType: TypeAlias = Union[ColorName, HexColor, RGBColor]

# ------------------------------------------------------------
# Color
# ------------------------------------------------------------


@dataclass
class Color:
    """Optimized color class with caching and fast lookups."""

    _value: Union[ColorName, HexColor, RGBColor]
    _rich_color: _RichColorClass | None = None
    _style: Style | None = None
    _cache: ClassVar[Dict[Union[str, RGBColor], "Color"]] = {}

    def __post_init__(self):
        """Initialize rich color immediately to avoid lazy loading."""
        if self._rich_color is None:
            if isinstance(self._value, str):
                # Prefer Rich color names to preserve the name in string representation
                if self._value in _RICH_COLOR_NAMES:
                    self._rich_color = _RichColorClass.parse(self._value)
                elif self._value in _PYDANTIC_COLOR_NAMES:
                    rgb = _COLORS_BY_NAME[self._value]
                    self._rich_color = _RichColorClass.from_rgb(rgb[0], rgb[1], rgb[2])
                else:
                    self._rich_color = _RichColorClass.parse(self._value)
            elif isinstance(self._value, tuple):
                self._rich_color = _RichColorClass.from_rgb(
                    self._value[0], self._value[1], self._value[2]
                )

    @classmethod
    def create(cls, color: ColorType) -> Self:
        """Creates a new color instance by parsing a given input color
        object.

        Examples:
            >>> Color.create("blue")
            >>> Color.create("#0000FF")
            >>> Color.create((0, 0, 255))

        Args:
            color: The color to create an instance of.

        Returns:
            A new color instance.
        """
        # Check cache first
        cache_key = color if isinstance(color, (str, tuple)) else str(color)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Create new instance
        if isinstance(color, str):
            if color in _ALL_COLOR_NAMES:
                instance = cls.from_name(color)
            else:
                instance = cls.from_hex(color)
        elif isinstance(color, tuple):
            instance = cls.from_rgb(color)
        else:
            raise ValueError(f"Invalid color type: {type(color)}")

        # Cache and return
        cls._cache[cache_key] = instance
        return instance

    @classmethod
    def from_name(cls, name: ColorName) -> Self:
        """Creates a new color instance by parsing a given color name.

        Examples:
            >>> Color.from_name("blue")
            >>> Color.from_name("red")
            >>> Color.from_name("green")
        """
        # Prefer Rich color names to preserve the name in string representation
        if name in _RICH_COLOR_NAMES:
            rich_color = _RichColorClass.parse(name)
        elif name in _PYDANTIC_COLOR_NAMES:
            rgb = _COLORS_BY_NAME[name]
            rich_color = _RichColorClass.from_rgb(rgb[0], rgb[1], rgb[2])
        else:
            rich_color = _RichColorClass.parse(name)

        return cls(_value=name, _rich_color=rich_color)

    @classmethod
    def from_hex(cls, hex_color: HexColor) -> Self:
        """Direct hex parsing."""
        return cls(_value=hex_color, _rich_color=_RichColorClass.parse(hex_color))

    @classmethod
    def from_rgb(cls, rgb: RGBColor) -> Self:
        """Direct RGB conversion."""
        return cls(
            _value=rgb, _rich_color=_RichColorClass.from_rgb(rgb[0], rgb[1], rgb[2])
        )

    @property
    def rich_color(self) -> _RichColorClass:
        """Direct access to rich color."""
        return self._rich_color

    def wrap(
        self,
        message: Any,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        blink2: Optional[bool] = None,
        reverse: Optional[bool] = None,
        conceal: Optional[bool] = None,
        strike: Optional[bool] = None,
        underline2: Optional[bool] = None,
        frame: Optional[bool] = None,
        encircle: Optional[bool] = None,
        overline: Optional[bool] = None,
        link: Optional[str] = None,
        **kwargs: Any,
    ) -> Text:
        """Creates a new tag with the given style.

        Examples:
            >>> color = Color.from_name("blue")
            >>> color.tag("Hello, World!")
            >>> color.tag("Hello, World!", bold=True)
        """
        # Create style key for caching
        style_key = (
            bold,
            dim,
            italic,
            underline,
            blink,
            blink2,
            reverse,
            conceal,
            strike,
            underline2,
            frame,
            encircle,
            overline,
            link,
        )

        # Check if we already have this style
        if self._style is None or style_key != getattr(self, "_last_style_key", None):
            self._style = Style(
                color=self._rich_color,
                bold=bold,
                dim=dim,
                italic=italic,
                underline=underline,
                blink=blink,
                blink2=blink2,
                reverse=reverse,
                conceal=conceal,
                strike=strike,
                underline2=underline2,
                frame=frame,
                encircle=encircle,
                overline=overline,
                link=link,
            )
            self._last_style_key = style_key

        return Text(text=str(message), style=self._style, **kwargs)

    def __str__(self) -> str:
        """Fast string conversion."""
        # Return appropriate string representation based on the original value type
        if isinstance(self._value, str):
            # If it's a rich color name, return the name
            if self._value in _RICH_COLOR_NAMES:
                return self._value
            # If it's a pydantic-only color name, return hex
            elif self._value in _PYDANTIC_COLOR_NAMES:
                return self._rich_color.get_truecolor().hex
            # If it's a hex string, return lowercase hex
            else:
                return self._value.lower()
        elif isinstance(self._value, tuple):
            # For RGB tuples, return hex representation
            return self._rich_color.get_truecolor().hex
        else:
            # Fallback to rich color string representation
            return str(self._rich_color)


if __name__ == "__main__":
    from rich import print

    color = Color.from_name("blue")
    print(color.wrap("Hello, World!"))

    color2 = Color.create("blue")
    print(color2.wrap("Cached color!"))
