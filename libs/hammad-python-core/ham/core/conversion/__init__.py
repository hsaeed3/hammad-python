"""ham.core.conversion

```markdown
Contains simplified utilities (mostly wrappers) for converting between different
standard pythonic objects and formats.
```
"""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer

if TYPE_CHECKING:
    from .models.converters import convert_to_model
    from .json import convert_to_json_schema
    from .text import convert_to_text, convert_type_to_text, convert_docstring_to_text


__all__ = (
    # ham.core.conversion.models
    "convert_to_model",
    # ham.core.conversion.json
    "convert_to_json_schema",
    # ham.core.conversion.text
    "convert_to_text",
    "convert_type_to_text",
    "convert_docstring_to_text",
)

__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
