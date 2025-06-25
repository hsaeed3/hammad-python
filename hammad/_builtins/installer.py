"""hammad.core.builtins.installer

Contains the `install` function which is used just for
swapping a few builtin methods with opinionated versions"""

import builtins
import sys
from rich.traceback import install as rich_traceback_install
from uvloop import install as uvloop_install

from ._input import input as hammad_input
from ._print import print as hammad_print

__all__ = ("install",)


base_print = builtins.print
base_input = builtins.input


def install(
    install_print: bool = True,
    install_input: bool = True,
    install_traceback: bool = True,
    install_uvloop: bool = True,
) -> None:
    """'Installs' a set of builtin optimizations or opinionated
    extensions based on a set of flags.

    Args:
        install_print : Whether to install the styled `print` function.
        install_input : Whether to install the stylized `input` function.
        install_traceback : Whether to install the rich traceback.
        install_uvloop : Whether to install the uvloop event loop.
    """
    if install_print:
        builtins.print = hammad_print
    if install_input:
        builtins.input = hammad_input
    if install_traceback:
        rich_traceback_install()
    if install_uvloop:
        uvloop_install()
