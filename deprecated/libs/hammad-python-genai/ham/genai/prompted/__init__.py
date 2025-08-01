"""ham.genai.prompted

```markdown
## `prompted`

This is the 'nightly' or internal implementation of the `prompted`
package that uses `ham.genai` resources.
```
"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ...core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from .core import (
        PromptedAgent,
        PromptedContext,
        PromptedFunction,
        PromptedIterator,
        PromptedResponse,
        PromptedStream,
        prompted as prompted_fn,
        contextualize,
        itemize,
    )
    from .selection import SelectionStrategy, select
    from .tools import Tool, tool


__all__ = (
    # ham.genai.prompted.core
    "PromptedAgent",
    "PromptedContext",
    "PromptedFunction",
    "PromptedIterator",
    "PromptedResponse",
    "PromptedStream",
    "prompted_fn",
    "contextualize",
    "itemize",
    # ham.genai.prompted.selection
    "SelectionStrategy",
    "select",
    # ham.genai.prompted.tools
    "Tool",
    "tool",
    # ham.genai.prompted.agent
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
