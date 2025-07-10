"""hammad.genai"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .embedding_models import (
        EmbeddingModel,
        EmbeddingModelRequest,
        EmbeddingModelResponse,
        run_embedding_model,
        async_run_embedding_model
    )
    from .language_models import (
        LanguageModel,
        LanguageModelRequest,
        LanguageModelResponse,
        run_language_model,
        async_run_language_model,
    )
    from .rerank_models import (
        run_rerank_model,
        async_run_rerank_model,
    )
    from .multimodal_models import (
        run_image_generation_model,
        async_run_image_generation_model,
        run_image_edit_model,
        async_run_image_edit_model,
        run_image_variation_model,
        async_run_image_variation_model,

        run_tts_model,
        async_run_tts_model,
        run_transcription_model,
        async_run_transcription_model,
    )


__all__ = (
    # hammad.genai.embedding_models
    "EmbeddingModel",
    "EmbeddingModelRequest",
    "EmbeddingModelResponse",
    "run_embedding_model",
    "async_run_embedding_model",

    # hammad.genai.language_models
    "LanguageModel",
    "LanguageModelRequest",
    "LanguageModelResponse",
    "run_language_model",
    "async_run_language_model",

    # hammad.genai.rerank_models
    "run_rerank_model",
    "async_run_rerank_model",

    # hammad.genai.multimodal_models
    "run_image_generation_model",
    "async_run_image_generation_model",
    "run_image_edit_model",
    "async_run_image_edit_model",
    "run_image_variation_model",
    "async_run_image_variation_model",
    "run_tts_model",
    "async_run_tts_model",
    "run_transcription_model",
    "async_run_transcription_model",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the genai module."""
    return list(__all__)