"""hammad.types.text

Contains the `Text` type, which is a functional type & object
for created intelligently rendered strings and markdown strings
from various input types and objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from ..settings import TextSettings
from ..utils.text_utils import convert_to_text, convert_type_to_text, convert_docstring_to_text


@dataclass
class Text:
    """A structured template object for creating clean text representations of
    various python objects and types."""

    text : str = field(default = "")
    """The text content within this object."""

    def __str__(self) -> str:
        """Returns the text content of this object."""
        return self.text
    
    def __repr__(self) -> str:
        """Returns the string representation of this object."""
        return f"Text(text={self.text!r})"
    
    def __eq__(self, other : Any) -> bool:
        """Checks if this object is equal to another object."""
        return self.text == other.text

    @classmethod
    def from_type(
        cls,
        type : Any
    ) -> Text:
        """Creates a `Text` object from a given type.
        
        Args:
            type : The type to create a `Text` object from.
        """
        return cls(text = convert_type_to_text(type))
    
    @classmethod
    def from_docstring(
        cls,
        obj : Any
    ) -> Text:
        """Creates a `Text` object from a given object's docstring.
        
        Args:
            obj : The object to create a `Text` object from.
        """
        return cls(text = convert_docstring_to_text(obj))

    @classmethod
    def from_text(
        cls,
        text : str
    ) -> Text:
        """Creates a `Text` object from a given string of text.
        
        Args:
            text : The text to create a `Text` object from.
        
        Returns:
            A `Text` object with the given text.
        """
        return cls(text = text)

    @classmethod
    def from_object(
        cls,
        obj : Any,
        prefix : str = "",
        suffix : str = "",
        title : str | None = None,
        description : str | None = None,
        examples : str | list[str] | None = None,
        # ------------------------------------------------------------
        # Primary Formatting Params
        # ------------------------------------------------------------
        code_block : bool = False,
        compact : bool = False,
        indent : int = 0,
        bullet_style : Literal["-", "*", "+", ">"] | str = "-",
        title_style : Literal["<>", "[]", "{}", "#"] | str = "##",
        # ------------------------------------------------------------
        # Definitions
        # ------------------------------------------------------------
        show_types : bool = True,
        show_values : bool = True,
        show_capital_titles : bool = False,
        show_description : bool = True,
        show_field_descriptions : bool = True,
        show_examples : bool = True,
        show_defaults : bool = True,
        show_required : bool = True,
        show_json_schema : bool = True,
        settings : TextSettings | None = None,
    ) -> Text:
        """Converts an object into a cleanly rendered `Text` representation
        using a specified set of parameters or a dictionary of settings.
        
        Args:
            obj : The object to convert to text.
            prefix : The prefix to use for the output.
            suffix : The suffix to use for the output.
            title : The title to use for the output.
            description : The description to use for the output.
            examples : The examples to include in the output.
            code_block : Whether to include a code block in the output.
            compact : Whether to include the compact representation of the object in the output.
            indent : The number of spaces to indent the output.
            bullet_style : The style to use for the bullet.
            title_style : The style to use for the title.
            show_types : Whether to include the types of the object in the output.
            show_values : Whether to include the values of the object in the output.
            show_capital_titles : Whether to include the capital titles of the object in the output.
            show_description : Whether to include the description of the object in the output.
            show_field_descriptions : Whether to include the field descriptions of the object in the output.
            show_examples : Whether to include the examples of the object in the output.
            show_defaults : Whether to include the default values of the object in the output.
            show_required : Whether to include the required fields of the object in the output.
            show_json_schema : Whether to include the JSON schema of the object in the output.
            settings : A dictionary of settings to use for the conversion.

        Returns:
            A `Text` object with the converted text.
        """
        if settings is None:
            return cls(
                text = convert_to_text(
                    obj = obj,
                    prefix = prefix,
                    suffix = suffix,
                    title = title,
                    description = description,
                    examples = examples,
                    code_block = code_block,
                    compact = compact,
                    indent = indent,
                    bullet_style = bullet_style,
                    title_style = title_style,
                    show_types = show_types,
                    show_values = show_values,
                    show_capital_titles = show_capital_titles,
                    show_description = show_description,
                    show_field_descriptions = show_field_descriptions,
                    show_examples = show_examples,
                    show_defaults = show_defaults,
                    show_required = show_required,
                    show_json_schema = show_json_schema,
                )
            )
        else:
            return cls(
                text = convert_to_text(
                    obj = obj,
                    prefix = settings.get("prefix", prefix),
                    suffix = settings.get("suffix", suffix),
                    title = settings.get("title", title),
                    description = settings.get("description", description),
                    examples = settings.get("examples", examples),
                    code_block = settings.get("code_block", code_block),
                    compact = settings.get("compact", compact),
                    indent = settings.get("indent", indent),
                    bullet_style = settings.get("bullet_style", bullet_style),
                    title_style = settings.get("title_style", title_style),
                    show_types = settings.get("show_types", show_types),
                    show_values = settings.get("show_values", show_values),
                    show_capital_titles = settings.get("show_capital_titles", show_capital_titles),
                    show_description = settings.get("show_description", show_description),
                    show_field_descriptions = settings.get("show_field_descriptions", show_field_descriptions),
                    show_examples = settings.get("show_examples", show_examples),
                    show_defaults = settings.get("show_defaults", show_defaults),
                    show_required = settings.get("show_required", show_required),
                    show_json_schema = settings.get("show_json_schema", show_json_schema),
                )
            )
        


