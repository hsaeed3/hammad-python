"""hammad.logging.tracers"""

from functools import wraps, update_wrapper
from typing import (
    Any,
    Callable,
    ParamSpec,
    TypeVar,
    List,
    overload,
    Union,
    Type,
    Dict,
    Optional,
)

import logging
import time
import inspect
from .logger import Logger, create_logger, LoggerLevelName
from ..cli.styles.types import (
    CLIStyleType,
    CLIStyleBackgroundType,
)


_P = ParamSpec("_P")
_R = TypeVar("_R")

__all__ = (
    "trace_function",
    "trace_cls",
    "trace",
)


def trace_function(
    fn: Optional[Callable[_P, _R]] = None,
    *,
    parameters: List[str] = [],
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "white",
    bg: Union[CLIStyleBackgroundType, str] = None,
) -> Union[Callable[_P, _R], Callable[[Callable[_P, _R]], Callable[_P, _R]]]:
    """
    Tracing decorator that logs the execution of any function, including
    class methods.

    You can optionally specify specific parameters, that will display
    'live updates' of the parameter values as they change.

    Args:
        fn: The function to trace.
        parameters: The parameters to trace.
        logger: The logger to use.
        level: The level to log at.
        rich: Whether to use rich for the logging.
        style: The style to use for the logging. This can be a string, or a dictionary
            of style settings.
        bg: The background to use for the logging. This can be a string, or a dictionary
            of background settings.

    Returns:
        The decorated function or a decorator function.
    """

    def decorator(target_fn: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(target_fn)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            # Get or create logger
            if logger is None:
                _logger = create_logger(
                    name=f"trace.{target_fn.__module__}.{target_fn.__name__}",
                    level=level,
                    rich=rich,
                )
            elif isinstance(logger, Logger):
                _logger = logger
            else:
                # It's a standard logging.Logger, wrap it
                _logger = create_logger(name=logger.name)
                _logger._logger = logger

            # Get function signature for parameter tracking
            sig = inspect.signature(target_fn)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Build entry message
            func_name = target_fn.__name__
            module_name = target_fn.__module__

            if rich and bg:
                # Create a styled panel for function entry
                entry_msg = f"[{style}]→ Entering {module_name}.{func_name}()[/{style}]"
            else:
                entry_msg = f"→ Entering {module_name}.{func_name}()"

            # Log parameters if requested
            if parameters:
                param_info = []
                for param in parameters:
                    if param in bound_args.arguments:
                        value = bound_args.arguments[param]
                        param_info.append(f"{param}={repr(value)}")

                if param_info:
                    entry_msg += f"\n  Parameters: {', '.join(param_info)}"

            # Log function entry
            _logger.log(level, entry_msg)

            # Track execution time
            start_time = time.time()

            try:
                # Execute the function
                result = target_fn(*args, **kwargs)

                # Calculate execution time
                exec_time = time.time() - start_time

                # Build exit message
                if rich and bg:
                    exit_msg = f"[{style}]← Exiting {module_name}.{func_name}() [dim](took {exec_time:.3f}s)[/dim][/{style}]"
                else:
                    exit_msg = (
                        f"← Exiting {module_name}.{func_name}() (took {exec_time:.3f}s)"
                    )

                # Log the result if it's not None
                if result is not None:
                    exit_msg += f"\n  Result: {repr(result)}"

                _logger.log(level, exit_msg)

                return result

            except Exception as e:
                # Calculate execution time
                exec_time = time.time() - start_time

                # Build error message
                error_style = "bold red" if rich else None
                if rich:
                    error_msg = f"[{error_style}]✗ Exception in {module_name}.{func_name}() [dim](after {exec_time:.3f}s)[/dim][/{error_style}]"
                    error_msg += f"\n  [red]{type(e).__name__}: {str(e)}[/red]"
                else:
                    error_msg = f"✗ Exception in {module_name}.{func_name}() (after {exec_time:.3f}s)"
                    error_msg += f"\n  {type(e).__name__}: {str(e)}"

                # Log at error level for exceptions
                _logger.error(error_msg)

                # Re-raise the exception
                raise

        return wrapper

    if fn is None:
        # Called with parameters: @trace_function(parameters=["x"])
        return decorator
    else:
        # Called directly: @trace_function
        return decorator(fn)


def trace_cls(
    cls: Optional[Type[Any]] = None,
    *,
    attributes: List[str] = [],
    functions: List[str] = [],
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "white",
    bg: Union[CLIStyleBackgroundType, str] = None,
) -> Union[Type[Any], Callable[[Type[Any]], Type[Any]]]:
    """
    Tracing decorator that logs the execution of any class, including
    class methods.

    Unlike the `trace_function` decorator, this decorator must take
    in either a list of attributes, or a list of functions to display
    'live updates' of the attribute values as they change.

    Args:
        cls: The class to trace.
        attributes: The attributes to trace.
        functions: The functions to trace.
        logger: An optional logger to use.
        level: An optional level to log at.
        rich: Whether to use rich for the logging.
        style: The style to use for the logging. This can be a string, or a dictionary
            of style settings.
        bg: The background to use for the logging. This can be a string, or a dictionary
            of background settings.

    Returns:
        The traced class or a decorator function.
    """

    def decorator(target_cls: Type[Any]) -> Type[Any]:
        # Get or create logger for the class
        if logger is None:
            _logger = create_logger(
                name=f"trace.{target_cls.__module__}.{target_cls.__name__}",
                level=level,
                rich=rich,
            )
        elif isinstance(logger, Logger):
            _logger = logger
        else:
            # It's a standard logging.Logger, wrap it
            _logger = create_logger(name=logger.name)
            _logger._logger = logger

        # Store original __init__ method
        original_init = target_cls.__init__

        # Create wrapper for __init__ to log instance creation and track attributes
        @wraps(original_init)
        def traced_init(self, *args, **kwargs):
            # Log instance creation
            if rich:
                create_msg = (
                    f"[{style}]🏗  Creating instance of {target_cls.__name__}[/{style}]"
                )
            else:
                create_msg = f"Creating instance of {target_cls.__name__}"

            _logger.log(level, create_msg)

            # Call original __init__
            original_init(self, *args, **kwargs)

            # Log initial attribute values if requested
            if attributes:
                attr_info = []
                for attr in attributes:
                    if hasattr(self, attr):
                        value = getattr(self, attr)
                        attr_info.append(f"{attr}={repr(value)}")

                if attr_info:
                    if rich:
                        attr_msg = f"[{style}]  Initial attributes: {', '.join(attr_info)}[/{style}]"
                    else:
                        attr_msg = f"  Initial attributes: {', '.join(attr_info)}"
                    _logger.log(level, attr_msg)

        # Replace __init__ with traced version
        target_cls.__init__ = traced_init

        # Create wrapper for __setattr__ to track attribute changes
        if attributes:
            original_setattr = (
                target_cls.__setattr__
                if hasattr(target_cls, "__setattr__")
                else object.__setattr__
            )

            def traced_setattr(self, name, value):
                # Check if this is a tracked attribute
                if name in attributes:
                    # Get old value if it exists
                    old_value = getattr(self, name, "<not set>")

                    # Call original __setattr__
                    if original_setattr == object.__setattr__:
                        object.__setattr__(self, name, value)
                    else:
                        original_setattr(self, name, value)

                    # Log the change
                    if rich:
                        change_msg = f"[{style}]{target_cls.__name__}.{name}: {repr(old_value)} → {repr(value)}[/{style}]"
                    else:
                        change_msg = f"{target_cls.__name__}.{name}: {repr(old_value)} → {repr(value)}"

                    _logger.log(level, change_msg)
                else:
                    # Not a tracked attribute, just set it normally
                    if original_setattr == object.__setattr__:
                        object.__setattr__(self, name, value)
                    else:
                        original_setattr(self, name, value)

            target_cls.__setattr__ = traced_setattr

        # Trace specific functions if requested
        if functions:
            for func_name in functions:
                if hasattr(target_cls, func_name):
                    func = getattr(target_cls, func_name)
                    if callable(func) and not isinstance(func, type):
                        # Apply trace_function decorator to this method
                        traced_func = trace_function(
                            func,
                            logger=_logger,
                            level=level,
                            rich=rich,
                            style=style,
                            bg=bg,
                        )
                        setattr(target_cls, func_name, traced_func)

        # Log class decoration
        if rich:
            decorate_msg = f"[{style}]✨ Decorated class {target_cls.__name__} with tracing[/{style}]"
        else:
            decorate_msg = f"Decorated class {target_cls.__name__} with tracing"

        _logger.log(level, decorate_msg)

        return target_cls

    if cls is None:
        # Called with parameters: @trace_cls(attributes=["x"])
        return decorator
    else:
        # Called directly: @trace_cls
        return decorator(cls)


# Decorator overloads for better type hints
@overload
def trace(
    func_or_cls: Callable[_P, _R],
) -> Callable[_P, _R]:
    """Decorator to add log tracing over a function or class."""


@overload
def trace(
    func_or_cls: Type[Any],
) -> Type[Any]:
    """Decorator to add log tracing over a class."""


@overload
def trace(
    *,
    parameters: List[str] = [],
    attributes: List[str] = [],
    functions: List[str] = [],
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "white",
    bg: Union[CLIStyleBackgroundType, str] = None,
) -> Callable[[Union[Callable[_P, _R], Type[Any]]], Union[Callable[_P, _R], Type[Any]]]:
    """Decorator to add log tracing over a function or class."""


def trace(
    func_or_cls: Union[Callable[_P, _R], Type[Any], None] = None,
    *,
    parameters: List[str] = [],
    attributes: List[str] = [],
    functions: List[str] = [],
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "bold blue",
    bg: Union[CLIStyleBackgroundType, str] = None,
) -> Union[
    Callable[_P, _R],
    Type[Any],
    Callable[[Union[Callable[_P, _R], Type[Any]]], Union[Callable[_P, _R], Type[Any]]],
]:
    """
    Universal tracing decorator that can be applied to both functions and classes.

    Can be used in three ways:
    1. @log (direct decoration)
    2. @log() (parameterized with defaults)
    3. @log(parameters=["x"], level="info") (parameterized with custom settings)

    When applied to a function, it logs entry/exit and optionally tracks parameters.
    When applied to a class, it can track attribute changes and log specific methods.

    Args:
        func_or_cls: The function or class to log (when used directly)
        parameters: For functions, the parameters to log
        attributes: For classes, the attributes to track changes
        functions: For classes, the methods to log
        logger: The logger to use (creates one if not provided)
        level: The logging level
        rich: Whether to use rich formatting
        style: The style for rich formatting
        bg: The background style for rich formatting

    Returns:
        The decorated function/class or a decorator function
    """

    def decorator(
        target: Union[Callable[_P, _R], Type[Any]],
    ) -> Union[Callable[_P, _R], Type[Any]]:
        if inspect.isclass(target):
            # It's a class
            return trace_cls(
                target,
                attributes=attributes,
                functions=functions,
                logger=logger,
                level=level,
                rich=rich,
                style=style,
                bg=bg,
            )
        else:
            # It's a function
            return trace_function(
                target,
                parameters=parameters,
                logger=logger,
                level=level,
                rich=rich,
                style=style,
                bg=bg,
            )

    if func_or_cls is None:
        # Called with parameters: @log(parameters=["x"])
        return decorator
    else:
        # Called directly: @log
        return decorator(func_or_cls)
