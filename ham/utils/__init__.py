"""ham.utils

General purpose utility functions and classes. Includes thing such as 
logging, caching, and other assorted helpers.

NOTE: Most public utilities within this framework are submodule-specific or categorized,
and live within their respective submodules."""


# NOTE: this is publically namespaced, but it's aliased only in this specific module
# to avoid circular import issues.
from .type_checking_getattr_fn import (
    type_checking_getattr_fn as _type_checking_getattr_fn,
    type_checking_dir_fn as _type_checking_dir_fn
)
from typing import TYPE_CHECKING


