"""hammad.types.color"""

from dataclasses import dataclass
from typing import ClassVar
from rich.color import Color as _RichColorClass
from rich.text import Text
from rich.style import Style
from typing import Any, Dict, Optional, Literal, Tuple, TypeAlias, Union, Self

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

# ------------------------------------------------------------
# Color Names
# ------------------------------------------------------------

_COLORS_BY_NAME: Dict[str, RGBColor] = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": (0, 0, 0),
    "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkgrey": (169, 169, 169),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "greenyellow": (173, 255, 47),
    "grey": (128, 128, 128),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": (0, 255, 0),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": (255, 0, 255),
    "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": (0, 0, 128),
    "oldlace": (253, 245, 230),
    "olive": (128, 128, 0),
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": (128, 0, 128),
    "red": (255, 0, 0),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": (192, 192, 192),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": (0, 128, 128),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": (255, 255, 255),
    "whitesmoke": (245, 245, 245),
    "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50),
}

_PYDANTIC_COLOR_NAMES = frozenset(_COLORS_BY_NAME.keys())

_RICH_COLOR_NAMES = frozenset(
    [
        "black",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "white",
        "bright_black",
        "bright_red",
        "bright_green",
        "bright_yellow",
        "bright_blue",
        "bright_magenta",
        "bright_cyan",
        "bright_white",
        "grey0",
        "navy_blue",
        "dark_blue",
        "blue3",
        "blue1",
        "dark_green",
        "deep_sky_blue4",
        "dodger_blue3",
        "dodger_blue2",
        "green4",
        "spring_green4",
        "turquoise4",
        "deep_sky_blue3",
        "dodger_blue1",
        "dark_cyan",
        "light_sea_green",
        "deep_sky_blue2",
        "deep_sky_blue1",
        "green3",
        "spring_green3",
        "cyan3",
        "dark_turquoise",
        "turquoise2",
        "green1",
        "spring_green2",
        "spring_green1",
        "medium_spring_green",
        "cyan2",
        "cyan1",
        "purple4",
        "purple3",
        "blue_violet",
        "grey37",
        "medium_purple4",
        "slate_blue3",
        "royal_blue1",
        "chartreuse4",
        "pale_turquoise4",
        "steel_blue",
        "steel_blue3",
        "cornflower_blue",
        "dark_sea_green4",
        "cadet_blue",
        "sky_blue3",
        "chartreuse3",
        "sea_green3",
        "aquamarine3",
        "medium_turquoise",
        "steel_blue1",
        "sea_green2",
        "sea_green1",
        "dark_slate_gray2",
        "dark_red",
        "dark_magenta",
        "orange4",
        "light_pink4",
        "plum4",
        "medium_purple3",
        "slate_blue1",
        "wheat4",
        "grey53",
        "light_slate_grey",
        "medium_purple",
        "light_slate_blue",
        "yellow4",
        "dark_sea_green",
        "light_sky_blue3",
        "sky_blue2",
        "chartreuse2",
        "pale_green3",
        "dark_slate_gray3",
        "sky_blue1",
        "chartreuse1",
        "light_green",
        "aquamarine1",
        "dark_slate_gray1",
        "deep_pink4",
        "medium_violet_red",
        "dark_violet",
        "purple",
        "medium_orchid3",
        "medium_orchid",
        "dark_goldenrod",
        "rosy_brown",
        "grey63",
        "medium_purple2",
        "medium_purple1",
        "dark_khaki",
        "navajo_white3",
        "grey69",
        "light_steel_blue3",
        "light_steel_blue",
        "dark_olive_green3",
        "dark_sea_green3",
        "light_cyan3",
        "light_sky_blue1",
        "green_yellow",
        "dark_olive_green2",
        "pale_green1",
        "dark_sea_green2",
        "pale_turquoise1",
        "red3",
        "deep_pink3",
        "magenta3",
        "dark_orange3",
        "indian_red",
        "hot_pink3",
        "hot_pink2",
        "orchid",
        "orange3",
        "light_salmon3",
        "light_pink3",
        "pink3",
        "plum3",
        "violet",
        "gold3",
        "light_goldenrod3",
        "tan",
        "misty_rose3",
        "thistle3",
        "plum2",
        "yellow3",
        "khaki3",
        "light_yellow3",
        "grey84",
        "light_steel_blue1",
        "yellow2",
        "dark_olive_green1",
        "dark_sea_green1",
        "honeydew2",
        "light_cyan1",
        "red1",
        "deep_pink2",
        "deep_pink1",
        "magenta2",
        "magenta1",
        "orange_red1",
        "indian_red1",
        "hot_pink",
        "medium_orchid1",
        "dark_orange",
        "salmon1",
        "light_coral",
        "pale_violet_red1",
        "orchid2",
        "orchid1",
        "orange1",
        "sandy_brown",
        "light_salmon1",
        "light_pink1",
        "pink1",
        "plum1",
        "gold1",
        "light_goldenrod2",
        "navajo_white1",
        "misty_rose1",
        "thistle1",
        "yellow1",
        "light_goldenrod1",
        "khaki1",
        "wheat1",
        "cornsilk1",
        "grey100",
        "grey3",
        "grey7",
        "grey11",
        "grey15",
        "grey19",
        "grey23",
        "grey27",
        "grey30",
        "grey35",
        "grey39",
        "grey42",
        "grey46",
        "grey50",
        "grey54",
        "grey58",
        "grey62",
        "grey66",
        "grey70",
        "grey74",
        "grey78",
        "grey82",
        "grey85",
        "grey89",
        "grey93",
    ]
)

_ALL_COLOR_NAMES = _PYDANTIC_COLOR_NAMES | _RICH_COLOR_NAMES

_RichColorName: TypeAlias = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
    "grey0",
    "navy_blue",
    "dark_blue",
    "blue3",
    "blue1",
    "dark_green",
    "deep_sky_blue4",
    "dodger_blue3",
    "dodger_blue2",
    "green4",
    "spring_green4",
    "turquoise4",
    "deep_sky_blue3",
    "dodger_blue1",
    "dark_cyan",
    "light_sea_green",
    "deep_sky_blue2",
    "deep_sky_blue1",
    "green3",
    "spring_green3",
    "cyan3",
    "dark_turquoise",
    "turquoise2",
    "green1",
    "spring_green2",
    "spring_green1",
    "medium_spring_green",
    "cyan2",
    "cyan1",
    "purple4",
    "purple3",
    "blue_violet",
    "grey37",
    "medium_purple4",
    "slate_blue3",
    "royal_blue1",
    "chartreuse4",
    "pale_turquoise4",
    "steel_blue",
    "steel_blue3",
    "cornflower_blue",
    "dark_sea_green4",
    "cadet_blue",
    "sky_blue3",
    "chartreuse3",
    "sea_green3",
    "aquamarine3",
    "medium_turquoise",
    "steel_blue1",
    "sea_green2",
    "sea_green1",
    "dark_slate_gray2",
    "dark_red",
    "dark_magenta",
    "orange4",
    "light_pink4",
    "plum4",
    "medium_purple3",
    "slate_blue1",
    "wheat4",
    "grey53",
    "light_slate_grey",
    "medium_purple",
    "light_slate_blue",
    "yellow4",
    "dark_sea_green",
    "light_sky_blue3",
    "sky_blue2",
    "chartreuse2",
    "pale_green3",
    "dark_slate_gray3",
    "sky_blue1",
    "chartreuse1",
    "light_green",
    "aquamarine1",
    "dark_slate_gray1",
    "deep_pink4",
    "medium_violet_red",
    "dark_violet",
    "purple",
    "medium_orchid3",
    "medium_orchid",
    "dark_goldenrod",
    "rosy_brown",
    "grey63",
    "medium_purple2",
    "medium_purple1",
    "dark_khaki",
    "navajo_white3",
    "grey69",
    "light_steel_blue3",
    "light_steel_blue",
    "dark_olive_green3",
    "dark_sea_green3",
    "light_cyan3",
    "light_sky_blue1",
    "green_yellow",
    "dark_olive_green2",
    "pale_green1",
    "dark_sea_green2",
    "pale_turquoise1",
    "red3",
    "deep_pink3",
    "magenta3",
    "dark_orange3",
    "indian_red",
    "hot_pink3",
    "hot_pink2",
    "orchid",
    "orange3",
    "light_salmon3",
    "light_pink3",
    "pink3",
    "plum3",
    "violet",
    "gold3",
    "light_goldenrod3",
    "tan",
    "misty_rose3",
    "thistle3",
    "plum2",
    "yellow3",
    "khaki3",
    "light_yellow3",
    "grey84",
    "light_steel_blue1",
    "yellow2",
    "dark_olive_green1",
    "dark_sea_green1",
    "honeydew2",
    "light_cyan1",
    "red1",
    "deep_pink2",
    "deep_pink1",
    "magenta2",
    "magenta1",
    "orange_red1",
    "indian_red1",
    "hot_pink",
    "medium_orchid1",
    "dark_orange",
    "salmon1",
    "light_coral",
    "pale_violet_red1",
    "orchid2",
    "orchid1",
    "orange1",
    "sandy_brown",
    "light_salmon1",
    "light_pink1",
    "pink1",
    "plum1",
    "gold1",
    "light_goldenrod2",
    "navajo_white1",
    "misty_rose1",
    "thistle1",
    "yellow1",
    "light_goldenrod1",
    "khaki1",
    "wheat1",
    "cornsilk1",
    "grey100",
    "grey3",
    "grey7",
    "grey11",
    "grey15",
    "grey19",
    "grey23",
    "grey27",
    "grey30",
    "grey35",
    "grey39",
    "grey42",
    "grey46",
    "grey50",
    "grey54",
    "grey58",
    "grey62",
    "grey66",
    "grey70",
    "grey74",
    "grey78",
    "grey82",
    "grey85",
    "grey89",
    "grey93",
]

_PydanticColorName: TypeAlias = Literal[
    "aliceblue",
    "antiquewhite",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgreen",
    "darkgrey",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "green",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgreen",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "red",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]

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
