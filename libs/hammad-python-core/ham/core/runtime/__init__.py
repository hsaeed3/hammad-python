"""ham.core.runtime"""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer


if TYPE_CHECKING:
    from .decorators import (
        sequentialize_function,
        parallelize_function,
        update_batch_type_hints,
    )
    from .run import run_sequentially, run_parallel, run_with_retry


__all__ = (
    # ham.core.runtime.decorators
    "sequentialize_function",
    "parallelize_function",
    "update_batch_type_hints",
    # ham.core.runtime.run
    "run_sequentially",
    "run_parallel",
    "run_with_retry",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
