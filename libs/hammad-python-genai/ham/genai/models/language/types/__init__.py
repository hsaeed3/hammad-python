"""ham.genai.models.language.types"""

from typing import TYPE_CHECKING

try:
    from ham.core._internal import type_checking_importer
except ImportError:
    from ....core._internal import type_checking_importer  # type: ignore

if TYPE_CHECKING:
    from .language_model_instructor_mode import LanguageModelInstructorMode
    from .language_model_messages import LanguageModelMessages
    from .language_model_name import LanguageModelName
    from .language_model_request import LanguageModelRequest
    from .language_model_response import LanguageModelResponse
    from .language_model_response_chunk import LanguageModelResponseChunk
    from .language_model_settings import LanguageModelSettings
    from .language_model_stream import LanguageModelStream

__all__ = [
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


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return __all__
