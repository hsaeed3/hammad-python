"""hammad.runtime"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer


if TYPE_CHECKING:
    from .decorators import (
        sequentialize_function,
        parallelize_function,
        update_batch_type_hints,
    )
    from .run import run_sequentially, run_parallel, run_with_retry


__all__ = (
    # hammad.performance.decorators
    "sequentialize_function",
    "parallelize_function",
    "update_batch_type_hints",
    # hammad.performance.run
    "run_sequentially",
    "run_parallel",
    "run_with_retry",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
