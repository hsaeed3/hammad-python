"""hammad.settings

Unified namespace for the various `Settings` dictionaries
available within the `hammad` package."""

from typing_extensions import TypedDict

__all__ = (
    "TextSettings",
)


# ------------------------------------------------------------
# TEXT
# ------------------------------------------------------------


class TextSettings(TypedDict, total = False):
    """Typed settings dictionary for the parameters used when converting
    objects to 'structured' string representations.
    
    NOTE:
    The usage of 'structured' in this case does not mean the object itself
    returned is structured, but rather the string representation of the object
    is structured in a way that is easy to read and understand."""

    title : str | None = None
    """The title of the object."""
    description : str | None = None
    """The description of the object."""
    prefix : str | None = None
    """The prefix to use for the output."""
    suffix : str | None = None
    """The suffix to use for the output."""
    examples : list[str] | str | None = None
    """The examples to include in the output."""
    code_block : bool = False
    """Whether to include a code block in the output."""
    compact : bool = False
    """Whether to include the compact representation of the object in the output."""
    indent : int = 0
    """The number of spaces to indent the output."""
    bullet_style : str = "•"
    """The style to use for the bullet."""
    title_style : str = "##"
    """The style to use for the title."""
    show_types : bool = True
    """Whether to include the types of the object in the output."""
    show_values : bool = False
    """Whether to include the values of the object in the output."""
    show_capital_titles : bool = False
    """Whether to include the capital titles of the object in the output."""
    show_description : bool = True
    """Whether to include the description of the object in the output."""
    show_field_descriptions : bool = True
    """Whether to include the field descriptions of the object in the output."""
    show_examples : bool = True
    """Whether to include the examples of the object in the output."""
    show_defaults : bool = True
    """Whether to include the default values of the object in the output."""
    show_required : bool = False
    """Whether to include the required fields of the object in the output."""
    show_json_schema : bool = False
    """Whether to include the JSON schema in the output."""