"""hammad._builtins

Contains the `builtins` extensions provided by the package.
This resource includes the `print`, `input` and `install`
extensions for using the various builtins of the package.

All resources within this module are meant to be used from
the top level of the package."""

import sys
from importlib import import_module

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .installer import install
    from ._input import (
        input,
        input_bool,
        input_confirm,
        input_float,
        input_int,
        input_json,
    )
    from ._print import print

__all__ = (
    "install",
    "input",
    "input_bool",
    "input_confirm",
    "input_float",
    "input_int",
    "input_json",
    "print",
)


def __getattr__(name: str):
    IMPORT_MAP: dict[str, tuple[str, str]] = {
        # hammad._builtins.installer
        "install": (".installer", "install"),
        # hammad._builtins._input
        "input": ("._input", "input"),
        "input_bool": ("._input", "input_bool"),
        "input_confirm": ("._input", "input_confirm"),
        "input_float": ("._input", "input_float"),
        "input_int": ("._input", "input_int"),
        "input_json": ("._input", "input_json"),
        # hammad._builtins._print
        "print": ("._print", "print"),
    }

    for name in IMPORT_MAP:
        module_path, attr_name = IMPORT_MAP[name]
        module = import_module(f"hammad._builtins{module_path}")
        if not hasattr(module, attr_name):
            raise AttributeError(
                f"module '{module.__name__}' has no attribute '{attr_name}'"
            )
        return getattr(module, attr_name)

    raise AttributeError(f"module 'hammad._builtins' has no attribute '{name}'")


def __dir__() -> list[str]:
    return list(__all__)
