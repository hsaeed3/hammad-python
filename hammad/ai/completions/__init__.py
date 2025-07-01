"""hammad.ai.completions

Contains types and model like objects for working with language model
completions."""

from typing import TYPE_CHECKING
from ...performance.imports import create_getattr_importer

if TYPE_CHECKING:
    from .client import CompletionsClient
    from .types import (
        Completion,
        CompletionChunk,
        CompletionStream,
        AsyncCompletionStream,
        CompletionsInputParam,
        CompletionsModelName,
        CompletionsOutputType,
    )
    from .settings import CompletionsSettings, CompletionsModelSettings
    from .create import create_completion, async_create_completion


__all__ = (
    # hammad.ai.completions.client
    "CompletionsClient",
    # hammad.ai.completions.types
    "Completion",
    "CompletionChunk",
    "CompletionStream",
    "AsyncCompletionStream",
    "CompletionsInputParam",
    "CompletionsModelName",
    "CompletionsOutputType",
    # hammad.ai.completions.create
    "create_completion",
    "async_create_completion",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
