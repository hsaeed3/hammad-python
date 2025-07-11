"""hammad.genai.models.language"""

from typing import TYPE_CHECKING
from ...._internal import create_getattr_importer


if TYPE_CHECKING:
    from .model import (
        LanguageModel,
        create_language_model,
    )
    from .run import run_language_model, async_run_language_model
    from .types.language_model_instructor_mode import LanguageModelInstructorMode
    from .types.language_model_messages import LanguageModelMessages
    from .types.language_model_name import LanguageModelName
    from .types.language_model_request import LanguageModelRequest
    from .types.language_model_response import LanguageModelResponse
    from .types.language_model_response_chunk import LanguageModelResponseChunk
    from .types.language_model_settings import LanguageModelSettings
    from .types.language_model_stream import LanguageModelStream

__all__ = [
    # hammad.genai.models.language.model
    "LanguageModel",
    "create_language_model",
    # hammad.genai.models.language.run
    "run_language_model",
    "async_run_language_model",
    # hammad.genai.models.language.types.language_model_instructor_mode
    "LanguageModelInstructorMode",
    # hammad.genai.models.language.types.language_model_messages
    "LanguageModelMessages",
    # hammad.genai.models.language.types.language_model_name
    "LanguageModelName",
    # hammad.genai.models.language.types.language_model_request
    "LanguageModelRequest",
    # hammad.genai.models.language.types.language_model_response
    "LanguageModelResponse",
    # hammad.genai.models.language.types.language_model_response_chunk
    "LanguageModelResponseChunk",
    # hammad.genai.models.language.types.language_model_settings
    "LanguageModelSettings",
    # hammad.genai.models.language.types.language_model_stream
    "LanguageModelStream",
]


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return __all__
