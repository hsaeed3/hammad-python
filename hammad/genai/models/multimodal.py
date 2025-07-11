"""hammad.genai.models.multimodal"""

# simple litellm refs
# thanks litellm :)

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from litellm import (
        # images / image editing
        image_generation as run_image_generation_model,
        aimage_generation as async_run_image_generation_model,
        image_edit as run_image_edit_model,
        aimage_edit as async_run_image_edit_model,
        image_variation as run_image_variation_model,
        aimage_variation as async_run_image_variation_model,
        # audio / speech
        speech as run_tts_model,
        aspeech as async_run_tts_model,
        transcription as run_transcription_model,
        atranscription as async_run_transcription_model,
    )


__all__ = (
    # images / image editing
    "run_image_generation_model",
    "async_run_image_generation_model",
    "run_image_edit_model",
    "async_run_image_edit_model",
    "run_image_variation_model",
    "async_run_image_variation_model",
    # audio / speech
    "run_tts_model",
    "async_run_tts_model",
    "run_transcription_model",
    "async_run_transcription_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
