"""ham.core._internal._logging

Internal logging resources."""

import logging
import os
from rich.logging import RichHandler
from rich import get_console


class RichMarkupFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.CRITICAL:
            record.msg = f"[bold red]{record.msg}[/bold red]"
        elif record.levelno >= logging.ERROR:
            record.msg = f"[italic red]{record.msg}[/italic red]"
        elif record.levelno >= logging.WARNING:
            record.msg = f"[italic yellow]{record.msg}[/italic yellow]"
        elif record.levelno >= logging.INFO:
            record.msg = f"[white]{record.msg}[/white]"
        elif record.levelno >= logging.DEBUG:
            record.msg = f"[italic dim]{record.msg}[/italic dim]"
        return True


def _get_all_ham_loggers():
    """Get all loggers that start with 'ham'"""
    ham_loggers = []
    for name in logging.Logger.manager.loggerDict:
        if name.startswith("ham"):
            ham_loggers.append(logging.getLogger(name))
    # Always include the root ham logger
    ham_loggers.append(logging.getLogger("ham"))
    return ham_loggers


# Initialize the main ham logger
logger = logging.getLogger("ham")
handler = RichHandler(
    level=logging.DEBUG,
    console=get_console(),
    rich_tracebacks=True,
    show_time=False,
    show_path=False,
    markup=True,
)
handler.setFormatter(logging.Formatter("| [bold]{name}[/bold] - {message}", style="{"))
handler.addFilter(RichMarkupFilter())


if not any(isinstance(h, RichHandler) for h in logger.handlers):
    logger.addHandler(handler)


# Check environment variables for initial state
_debug = os.environ.get("HAM_LOGGING_DEBUG", "").lower() in ("true", "1", "yes")
_verbose = os.environ.get("HAM_LOGGING_VERBOSE", "").lower() in ("true", "1", "yes")


def _sync_all_ham_loggers():
    """Synchronize all ham.* loggers with current debug/verbose state"""
    if _debug:
        target_level = logging.DEBUG
    elif _verbose:
        target_level = logging.INFO
    else:
        target_level = logging.WARNING

    # Update all ham loggers
    for ham_logger in _get_all_ham_loggers():
        ham_logger.setLevel(target_level)
        ham_logger.propagate = True


def get_debug():
    """Get current debug state"""
    return _debug


def set_debug(value):
    """Set debug state"""
    global _debug, _verbose
    _debug = bool(value)
    if _debug:
        _verbose = True  # debug implies verbose
    _sync_all_ham_loggers()


def get_verbose():
    """Get current verbose state"""
    return _verbose


def set_verbose(value):
    """Set verbose state"""
    global _verbose
    _verbose = bool(value)
    _sync_all_ham_loggers()


# Create module-level properties
debug = property(get_debug, set_debug)
verbose = property(get_verbose, set_verbose)


# Initialize logger levels based on environment variables or defaults
_sync_all_ham_loggers()


# -----------------------------------------------------------------------------
# !! WARNINGS
# -----------------------------------------------------------------------------


def warn_deprecated(
    old_class: str | None = None,
    old_attribute: str | None = None,
    old_function: str | None = None,
    old_parameter: str | None = None,
    new_class: str | None = None,
    new_attribute: str | None = None,
    new_function: str | None = None,
    new_parameter: str | None = None,
) -> None:
    """Internal utility to warn about deprecated resources.

    Args:
        old : str
            The old resource name.
        new : str
            The new resource name.
    """
    logger = logging.getLogger("ham.core")
    # Determine the type of deprecation and construct the warning message
    if old_class and new_class:
        logger.warning(f"Class '{old_class}' is deprecated. Use '{new_class}' instead.")
    elif old_attribute and new_attribute:
        logger.warning(
            f"Attribute '{old_attribute}' is deprecated. Use '{new_attribute}' instead."
        )
    elif old_function and new_function:
        logger.warning(
            f"Function '{old_function}' is deprecated. Use '{new_function}' instead."
        )
    elif old_parameter and new_parameter:
        logger.warning(
            f"Parameter '{old_parameter}' is deprecated. Use '{new_parameter}' instead."
        )
    elif old_class:
        logger.warning(f"Class '{old_class}' is deprecated.")
    elif old_attribute:
        logger.warning(f"Attribute '{old_attribute}' is deprecated.")
    elif old_function:
        logger.warning(f"Function '{old_function}' is deprecated.")
    elif old_parameter:
        logger.warning(f"Parameter '{old_parameter}' is deprecated.")
    else:
        logger.warning("Deprecated usage detected.")


def raise_not_installed(
    module: str,
    packages: str | list[str],
    extensions: str | list[str],
) -> None:
    """
    Internal utility to raise an error if a module is not installed.

    Args:
        module : str
            The module name.
        packages : str | list[str]
            The package name(s).
        extensions : str | list[str]
            The extension name(s).
    """
    logger = logging.getLogger("ham.extensions")

    if isinstance(packages, str):
        packages = [packages]
    if isinstance(extensions, str):
        extensions = [extensions]

    logger.critical(
        f"Module '{module}' is not installed. "
        f"You can either:"
        f"1. Install required packages: {', '.join(packages)}. "
        f"2. Install either of the following extensions: {', '.join([f'hammad-python[{ext}]' for ext in extensions])}."
    )


__all__ = [
    "debug",
    "verbose",
    "logger",
    "get_debug",
    "set_debug",
    "get_verbose",
    "set_verbose",
    "_sync_all_ham_loggers",
    "_get_all_ham_loggers",
    "warn_deprecated",
    "raise_not_installed",
]
