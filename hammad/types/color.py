"""hammad.types.color"""

from dataclasses import dataclass
from rich.color import (
    Color as _RichColorClass,
)
from rich.text import Text
from rich.style import Style
from typing import (
    Any,
    Dict,
    Optional,
    Literal,
    Tuple,
    TypeAlias,
    Union,
    Self
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


HexColor : TypeAlias = str
"""Hexadecimal color string."""


RGBColor : TypeAlias = Tuple[int, int, int]
"""RGB Color Tuple Parameter & Type."""


# ------------------------------------------------------------
# Color Names
# ------------------------------------------------------------


_COLORS_BY_NAME : Dict[str, RGBColor] = {
    'aliceblue': (240, 248, 255),
    'antiquewhite': (250, 235, 215),
    'aqua': (0, 255, 255),
    'aquamarine': (127, 255, 212),
    'azure': (240, 255, 255),
    'beige': (245, 245, 220),
    'bisque': (255, 228, 196),
    'black': (0, 0, 0),
    'blanchedalmond': (255, 235, 205),
    'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226),
    'brown': (165, 42, 42),
    'burlywood': (222, 184, 135),
    'cadetblue': (95, 158, 160),
    'chartreuse': (127, 255, 0),
    'chocolate': (210, 105, 30),
    'coral': (255, 127, 80),
    'cornflowerblue': (100, 149, 237),
    'cornsilk': (255, 248, 220),
    'crimson': (220, 20, 60),
    'cyan': (0, 255, 255),
    'darkblue': (0, 0, 139),
    'darkcyan': (0, 139, 139),
    'darkgoldenrod': (184, 134, 11),
    'darkgray': (169, 169, 169),
    'darkgreen': (0, 100, 0),
    'darkgrey': (169, 169, 169),
    'darkkhaki': (189, 183, 107),
    'darkmagenta': (139, 0, 139),
    'darkolivegreen': (85, 107, 47),
    'darkorange': (255, 140, 0),
    'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0),
    'darksalmon': (233, 150, 122),
    'darkseagreen': (143, 188, 143),
    'darkslateblue': (72, 61, 139),
    'darkslategray': (47, 79, 79),
    'darkslategrey': (47, 79, 79),
    'darkturquoise': (0, 206, 209),
    'darkviolet': (148, 0, 211),
    'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255),
    'dimgray': (105, 105, 105),
    'dimgrey': (105, 105, 105),
    'dodgerblue': (30, 144, 255),
    'firebrick': (178, 34, 34),
    'floralwhite': (255, 250, 240),
    'forestgreen': (34, 139, 34),
    'fuchsia': (255, 0, 255),
    'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255),
    'gold': (255, 215, 0),
    'goldenrod': (218, 165, 32),
    'gray': (128, 128, 128),
    'green': (0, 128, 0),
    'greenyellow': (173, 255, 47),
    'grey': (128, 128, 128),
    'honeydew': (240, 255, 240),
    'hotpink': (255, 105, 180),
    'indianred': (205, 92, 92),
    'indigo': (75, 0, 130),
    'ivory': (255, 255, 240),
    'khaki': (240, 230, 140),
    'lavender': (230, 230, 250),
    'lavenderblush': (255, 240, 245),
    'lawngreen': (124, 252, 0),
    'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230),
    'lightcoral': (240, 128, 128),
    'lightcyan': (224, 255, 255),
    'lightgoldenrodyellow': (250, 250, 210),
    'lightgray': (211, 211, 211),
    'lightgreen': (144, 238, 144),
    'lightgrey': (211, 211, 211),
    'lightpink': (255, 182, 193),
    'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170),
    'lightskyblue': (135, 206, 250),
    'lightslategray': (119, 136, 153),
    'lightslategrey': (119, 136, 153),
    'lightsteelblue': (176, 196, 222),
    'lightyellow': (255, 255, 224),
    'lime': (0, 255, 0),
    'limegreen': (50, 205, 50),
    'linen': (250, 240, 230),
    'magenta': (255, 0, 255),
    'maroon': (128, 0, 0),
    'mediumaquamarine': (102, 205, 170),
    'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211),
    'mediumpurple': (147, 112, 219),
    'mediumseagreen': (60, 179, 113),
    'mediumslateblue': (123, 104, 238),
    'mediumspringgreen': (0, 250, 154),
    'mediumturquoise': (72, 209, 204),
    'mediumvioletred': (199, 21, 133),
    'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250),
    'mistyrose': (255, 228, 225),
    'moccasin': (255, 228, 181),
    'navajowhite': (255, 222, 173),
    'navy': (0, 0, 128),
    'oldlace': (253, 245, 230),
    'olive': (128, 128, 0),
    'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0),
    'orangered': (255, 69, 0),
    'orchid': (218, 112, 214),
    'palegoldenrod': (238, 232, 170),
    'palegreen': (152, 251, 152),
    'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147),
    'papayawhip': (255, 239, 213),
    'peachpuff': (255, 218, 185),
    'peru': (205, 133, 63),
    'pink': (255, 192, 203),
    'plum': (221, 160, 221),
    'powderblue': (176, 224, 230),
    'purple': (128, 0, 128),
    'red': (255, 0, 0),
    'rosybrown': (188, 143, 143),
    'royalblue': (65, 105, 225),
    'saddlebrown': (139, 69, 19),
    'salmon': (250, 128, 114),
    'sandybrown': (244, 164, 96),
    'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238),
    'sienna': (160, 82, 45),
    'silver': (192, 192, 192),
    'skyblue': (135, 206, 235),
    'slateblue': (106, 90, 205),
    'slategray': (112, 128, 144),
    'slategrey': (112, 128, 144),
    'snow': (255, 250, 250),
    'springgreen': (0, 255, 127),
    'steelblue': (70, 130, 180),
    'tan': (210, 180, 140),
    'teal': (0, 128, 128),
    'thistle': (216, 191, 216),
    'tomato': (255, 99, 71),
    'turquoise': (64, 224, 208),
    'violet': (238, 130, 238),
    'wheat': (245, 222, 179),
    'white': (255, 255, 255),
    'whitesmoke': (245, 245, 245),
    'yellow': (255, 255, 0),
    'yellowgreen': (154, 205, 50),
}


_RichColorName: TypeAlias = Literal[
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue", 
    "bright_magenta", "bright_cyan", "bright_white", "grey0", "navy_blue", "dark_blue",
    "blue3", "blue1", "dark_green", "deep_sky_blue4", "dodger_blue3", "dodger_blue2",
    "green4", "spring_green4", "turquoise4", "deep_sky_blue3", "dodger_blue1", 
    "dark_cyan", "light_sea_green", "deep_sky_blue2", "deep_sky_blue1", "green3",
    "spring_green3", "cyan3", "dark_turquoise", "turquoise2", "green1", "spring_green2",
    "spring_green1", "medium_spring_green", "cyan2", "cyan1", "purple4", "purple3",
    "blue_violet", "grey37", "medium_purple4", "slate_blue3", "royal_blue1", 
    "chartreuse4", "pale_turquoise4", "steel_blue", "steel_blue3", "cornflower_blue",
    "dark_sea_green4", "cadet_blue", "sky_blue3", "chartreuse3", "sea_green3",
    "aquamarine3", "medium_turquoise", "steel_blue1", "sea_green2", "sea_green1",
    "dark_slate_gray2", "dark_red", "dark_magenta", "orange4", "light_pink4", "plum4",
    "medium_purple3", "slate_blue1", "wheat4", "grey53", "light_slate_grey",
    "medium_purple", "light_slate_blue", "yellow4", "dark_sea_green", "light_sky_blue3",
    "sky_blue2", "chartreuse2", "pale_green3", "dark_slate_gray3", "sky_blue1",
    "chartreuse1", "light_green", "aquamarine1", "dark_slate_gray1", "deep_pink4",
    "medium_violet_red", "dark_violet", "purple", "medium_orchid3", "medium_orchid",
    "dark_goldenrod", "rosy_brown", "grey63", "medium_purple2", "medium_purple1",
    "dark_khaki", "navajo_white3", "grey69", "light_steel_blue3", "light_steel_blue",
    "dark_olive_green3", "dark_sea_green3", "light_cyan3", "light_sky_blue1",
    "green_yellow", "dark_olive_green2", "pale_green1", "dark_sea_green2",
    "pale_turquoise1", "red3", "deep_pink3", "magenta3", "dark_orange3", "indian_red",
    "hot_pink3", "hot_pink2", "orchid", "orange3", "light_salmon3", "light_pink3",
    "pink3", "plum3", "violet", "gold3", "light_goldenrod3", "tan", "misty_rose3",
    "thistle3", "plum2", "yellow3", "khaki3", "light_yellow3", "grey84",
    "light_steel_blue1", "yellow2", "dark_olive_green1", "dark_sea_green1", "honeydew2",
    "light_cyan1", "red1", "deep_pink2", "deep_pink1", "magenta2", "magenta1",
    "orange_red1", "indian_red1", "hot_pink", "medium_orchid1", "dark_orange",
    "salmon1", "light_coral", "pale_violet_red1", "orchid2", "orchid1", "orange1",
    "sandy_brown", "light_salmon1", "light_pink1", "pink1", "plum1", "gold1",
    "light_goldenrod2", "navajo_white1", "misty_rose1", "thistle1", "yellow1",
    "light_goldenrod1", "khaki1", "wheat1", "cornsilk1", "grey100", "grey3", "grey7",
    "grey11", "grey15", "grey19", "grey23", "grey27", "grey30", "grey35", "grey39",
    "grey42", "grey46", "grey50", "grey54", "grey58", "grey62", "grey66", "grey70",
    "grey74", "grey78", "grey82", "grey85", "grey89", "grey93"
]
"""Helper alias for Rich color names."""


_PydanticColorName: TypeAlias = Literal[
    "aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque",
    "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue",
    "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan",
    "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey",
    "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred",
    "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey",
    "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey",
    "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia", "gainsboro",
    "ghostwhite", "gold", "goldenrod", "gray", "green", "greenyellow", "grey",
    "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender",
    "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral", "lightcyan",
    "lightgoldenrodyellow", "lightgray", "lightgreen", "lightgrey", "lightpink",
    "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray", "lightslategrey",
    "lightsteelblue", "lightyellow", "lime", "limegreen", "linen", "magenta", "maroon",
    "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen",
    "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred",
    "midnightblue", "mintcream", "mistyrose", "moccasin", "navajowhite", "navy",
    "oldlace", "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod",
    "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff", "peru",
    "pink", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue",
    "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna", "silver",
    "skyblue", "slateblue", "slategray", "slategrey", "snow", "springgreen", "steelblue",
    "tan", "teal", "thistle", "tomato", "turquoise", "violet", "wheat", "white",
    "whitesmoke", "yellow", "yellowgreen"
]
"""Helper alias for Pydantic color names."""


ColorName : TypeAlias = Union[_RichColorName, _PydanticColorName]
"""Helper alias for color names from both the Rich and Pydantic libraries."""


# ------------------------------------------------------------
# Utils
# ------------------------------------------------------------


def _convert_name_to_rich_color_class(name : str) -> _RichColorClass:
    """Converts a color's name to a Rich color class.
    
    Compatible with color names from both the Rich and Pydantic libraries.

    Args:
        name (str): The name of the color to convert.

    Returns:
        _RichColorClass: The Rich color class.
    """
    if name in _PydanticColorName.__args__:
        r, g, b = _COLORS_BY_NAME[name]
        return _RichColorClass.from_rgb(r, g, b)
    
    else:
        # assume rich color
        # this raises an error if the color is invalid
        return _RichColorClass.parse(name)
    

def _convert_hex_to_rich_color_class(hex_color : str) -> _RichColorClass:
    """Converts a hex color string to a Rich color class.
    
    Args:
        hex_color (str): The hex color string to convert.

    Returns:
        _RichColorClass: The Rich color class.
    """
    try:
        return _RichColorClass.parse(hex_color)
    except ValueError:
        raise ValueError(f"Invalid hex color: {hex_color}")
    

def _convert_rgb_to_rich_color_class(rgb : RGBColor) -> _RichColorClass:
    """Converts an RGB color tuple to a Rich color class.

    EX: (255, 0, 0) -> red
    
    Args:
        rgb (RGBColor): The RGB color tuple to convert.

    Returns:
        _RichColorClass: The Rich color class.
    """
    return _RichColorClass.from_rgb(*rgb)


# ------------------------------------------------------------
# Color
# ------------------------------------------------------------


ColorType : TypeAlias = Union[ColorName, HexColor, RGBColor]
"""Helper alias for color types."""


@dataclass
class Color:
    """Helper class simply used to add literal type hinting, and
    more named colors to the `rich.color.Color` class, enabling
    easy use within `rich.print` and many of the styled
    resources within `hammadpy`."""

    _value : Union[ColorName, HexColor, RGBColor]
    """The original input value of the color."""

    _rich_color : _RichColorClass | None = None
    """The Rich color class instance."""

    _style : Style | None = None
    """The Rich style instance."""

    @classmethod
    def create(cls, color : ColorType) -> Self:
        """Creates a `Color` instance from a color name, hex color string, or RGB color tuple.

        Example : `Color("red")`
        Example : `Color("#FF0000")`
        Example : `Color((255, 0, 0))`
        
        Args:
            color (ColorType): The color to create.

        Returns:
            Color: The `Color` instance.
        """
        if color in ColorName.__args__:
            return cls.from_name(color)
        elif isinstance(color, str):
            return cls.from_hex(color)
        elif isinstance(color, tuple):
            return cls.from_rgb(color)
        else:
            raise ValueError(f"Invalid color type: {type(color)}")

    @classmethod
    def from_name(cls, name : ColorName) -> Self:
        """Creates a `Color` instance from a color name.
        
        Args:
            name (ColorName): The name of the color to create.

        Returns:
            Color: The `Color` instance.
        """
        return cls(
            _value = name,
            _rich_color = _convert_name_to_rich_color_class(name),
        )
    
    @classmethod
    def from_hex(cls, hex_color : HexColor) -> Self:
        """Creates a `Color` instance from a hex color string.
        
        Args:
            hex_color (HexColor): The hex color string to create.

        Returns:
            Color: The `Color` instance.
        """
        return cls(
            _value = hex_color,
            _rich_color = _convert_hex_to_rich_color_class(hex_color),
        )
    
    @classmethod
    def from_rgb(cls, rgb : RGBColor) -> Self:
        """Creates a `Color` instance from an RGB color tuple.
        """
        return cls(
            _value = rgb,
            _rich_color = _convert_rgb_to_rich_color_class(rgb),
        )
    
    @property
    def rich_color(self) -> _RichColorClass:
        """The Rich color class instance."""
        if self._rich_color is None:
            raise ValueError(f"Color instance has not been initialized with a Rich color class.")
        
        return self._rich_color
    
    def tag(
        self,
        message : Any,
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
        """Wraps a message in a Rich tag with the color.
        
        Args:
            message (Any): The message to tag.

        Returns:
            Text: The tagged message.
        """
        return Text(
            text = str(message),
            style = Style(
                color = self.rich_color,
                bold = bold,
                dim = dim,
                italic = italic,
                underline = underline,
                blink = blink,
                blink2 = blink2,
                reverse = reverse,
                conceal = conceal,
                strike = strike,
                underline2 = underline2,
                frame = frame,
                encircle = encircle,
                overline = overline,
                link = link,
            ),
            **kwargs,
        )
    
    def __str__(self) -> str:
        """Renders the color as a string that is usable within
        `rich.print` and many of the styled resources within
        `hammadpy`."""
        return str(self.rich_color)
    

if __name__ == "__main__":

    from rich import print

    color = Color.from_name("blue")

    print(color.tag('Hello, World!'))