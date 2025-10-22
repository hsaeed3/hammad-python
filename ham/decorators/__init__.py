"""ham.decorators"""

from ..utils.import_utils import (
    TYPE_CHECKING,
    type_checking_dir_fn,
    type_checking_getattr_fn,
)


if TYPE_CHECKING:
    # ham.utils.cache
    from ..utils.cache import cached


__all__ = (
    # ham.utils.cache
    "cached",
)


__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)
