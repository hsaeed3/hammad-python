"""hammad.genai.language_models"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .language_model import LanguageModel
    from .run import run_language_model, async_run_language_model
    from .language_model_request import LanguageModelMessagesParam
    from .language_model_response import LanguageModelResponse
    from .language_model_response_chunk import LanguageModelResponseChunk
    from .language_model_request import LanguageModelRequest

__all__ = (
    # hammad.genai.language_models.language_model
    "LanguageModel",

    # hammad.genai.language_models.run
    "run_language_model",
    "async_run_language_model",

    # hammad.genai.language_models.language_model_request
    "LanguageModelMessagesParam",
    "LanguageModelRequest",

    # hammad.genai.language_models.language_model_response
    "LanguageModelResponse",
    "LanguageModelResponseChunk",
)

__getattr__ = create_getattr_importer(__all__)

def __dir__() -> list[str]:
    """Get the attributes of the language_models module."""
    return list(__all__)