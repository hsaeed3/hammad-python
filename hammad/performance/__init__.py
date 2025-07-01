"""hammad.performance

Contains a collection of various utilities and resources for 'accelerating' or
optimizing different objects and operations in general Python development."""

from typing import TYPE_CHECKING
from .imports import create_getattr_importer


if TYPE_CHECKING:
    from .runtime import (
        sequentialize_function,
        parallelize_function,
        update_batch_type_hints,
        run_sequentially,
        run_parallel,
        run_with_retry,
    )


__all__ = (
    # hammad.performance.runtime
    "sequentialize_function",
    "parallelize_function",
    "update_batch_type_hints",
    "run_sequentially",
    "run_parallel",
    "run_with_retry",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return sorted(__all__)
