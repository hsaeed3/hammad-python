"""ham.functions.utils

Uncategorized utility functions and resources."""

from .import_utils import type_checking_dir_fn, type_checking_getattr_fn, TYPE_CHECKING


if TYPE_CHECKING:
    from .cache import cached, clear_cache


__all__ = (
    # NOTE:
    # this is the one place 'type_checking_getattr_fn' and
    # 'type_checking_dir_fn' are considered exports
    "type_checking_getattr_fn",
    "type_checking_dir_fn",
    # ham.functions.utils.cache
    "cached",
    "clear_cache",
)


__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)
