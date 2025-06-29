"""hammad.ai._utils

Shared internal utilities for the `hammad.ai` extension."""

from typing import Any, Optional, Sequence

__all__ = (
    "get_instructor",
    "get_litellm",
    "get_fastembed",
    "get_fastembed_text_embedding_model",
)


# ------------------------------------------------------------
# INSTRUCTOR
# ------------------------------------------------------------


INSTRUCTOR_MODULE = None
"""Library level singleton for the `instructor` module."""


def get_instructor():
    """Get the instructor module."""
    global INSTRUCTOR_MODULE

    if INSTRUCTOR_MODULE is None:
        try:
            import instructor

            INSTRUCTOR_MODULE = instructor
        except ImportError:
            raise ImportError(
                "instructor is not installed. Please install it with `pip install hammad-python[ai]`"
            )

    return INSTRUCTOR_MODULE


# ------------------------------------------------------------
# LITELLM
# ------------------------------------------------------------


LITELLM_MODULE = None
"""Library level singleton for the `litellm` module."""


def get_litellm():
    """Get the litellm module."""
    global LITELLM_MODULE
    if LITELLM_MODULE is None:
        try:
            import litellm

            litellm.drop_params = True
            litellm.modify_params = True
            LITELLM_MODULE = litellm
        except ImportError:
            raise ImportError(
                "litellm is not installed. Please install it with `pip install hammad-python[ai]`"
            )

    return LITELLM_MODULE


# ------------------------------------------------------------
# FASTEMBED
# ------------------------------------------------------------


FASTEMBED_MODULE = None
"""Library level singleton for the `fastembed` module."""


def get_fastembed():
    """Get the fastembed module."""
    global FASTEMBED_MODULE
    if FASTEMBED_MODULE is None:
        try:
            import fastembed

            FASTEMBED_MODULE = fastembed
        except ImportError:
            raise ImportError(
                "fastembed is not installed. Please install it with `pip install hammad-python[ai]`"
            )

    return FASTEMBED_MODULE


FASTEMBED_LOADED_TEXT_EMBEDDING_MODELS: dict = {}


def get_fastembed_text_embedding_model(
    model: str,
    cache_dir: Optional[str] = None,
    threads: Optional[int] = None,
    providers: Optional[Sequence[Any]] = None,
    cuda: bool = False,
    device_ids: Optional[list[int]] = None,
    lazy_load: bool = False,
):
    """Initializes a fastembed model instance for a given
    model name using a global library level singleton.

    NOTE: Custom models are not supported yet.

    Args:
        model (str) : The model name to load.
        cache_dir (Optional[str]) : The directory to cache the model in.
        threads (Optional[int]) : The number of threads to use for the model.
        providers (Optional[Sequence[Any]]) : The ONNX providers to use for the model.
        cuda (bool) : Whether to use CUDA for the model.
        device_ids (Optional[list[int]]) : The device IDs to use for the model.
        lazy_load (bool) : Whether to lazy load the model.

    Returns:
        fastembed.TextEmbedding : The loaded fastembed model instance.
    """
    global FASTEMBED_LOADED_TEXT_EMBEDDING_MODELS

    if model not in FASTEMBED_LOADED_TEXT_EMBEDDING_MODELS:
        fastembed_module = get_fastembed()

        try:
            embedding_model = fastembed_module.TextEmbedding(
                model_name=model,
                cache_dir=cache_dir,
                threads=threads,
                providers=providers,
                cuda=cuda,
                device_ids=device_ids,
                lazy_load=lazy_load,
            )
        except Exception as e:
            raise e

        FASTEMBED_LOADED_TEXT_EMBEDDING_MODELS[model] = embedding_model

    return FASTEMBED_LOADED_TEXT_EMBEDDING_MODELS[model]
