"""hammad._to

Top level namspace resource for converters."""


class to:
    """Converter resource"""

    from ..data import (
        convert_to_pydantic_field as pydantic_field,
        convert_to_pydantic_model as pydantic_model,
    )
    from ..formatting.json import (
        convert_to_json_schema as json_schema,
    )
    from ..formatting.text import convert_to_text as text


__all__ = "to"
