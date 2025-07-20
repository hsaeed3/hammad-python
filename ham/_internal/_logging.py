"""ham._internal._logging

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
        if name.startswith('ham'):
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
_debug = os.environ.get('HAM_LOGGING_DEBUG', '').lower() in ('true', '1', 'yes')
_verbose = os.environ.get('HAM_LOGGING_VERBOSE', '').lower() in ('true', '1', 'yes')


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


__all__ = ["debug", "verbose", "logger"]