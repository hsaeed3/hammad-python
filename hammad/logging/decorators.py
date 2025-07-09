"""hammad.logging.decorators"""

from functools import wraps
from typing import (
    Any,
    Callable,
    ParamSpec,
    TypeVar,
    List,
    overload,
    Union,
    Type,
    Optional,
    Awaitable,
)
import asyncio

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
    "trace_http",
    "install_trace_http",
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


def trace_http(
    fn_or_call: Union[Callable[_P, _R], Callable[_P, Awaitable[_R]], Any, None] = None,
    *,
    show_request: bool = True,
    show_response: bool = True,
    request_exclude_none: bool = True,
    response_exclude_none: bool = False,
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "white",
    bg: Union[CLIStyleBackgroundType, str] = None,  # noqa: ARG001
) -> Any:
    """Wraps any function that makes HTTP requests, and displays only the request / response
    bodies in a pretty panel. Can be used as a decorator or direct function wrapper.

    Usage patterns:
    1. As decorator: @trace_http
    2. As decorator with params: @trace_http(show_request=False)
    3. Direct function call: trace_http(my_function(), show_request=True)
    4. Direct async function call: await trace_http(my_async_function(), show_request=True)

    Args:
        fn_or_call: The function to wrap, or the result of a function call.
        show_request: Whether to show the request body.
        show_response: Whether to show the response body.
        request_exclude_none: Whether to exclude None values from request logging.
        response_exclude_none: Whether to exclude None values from response logging.
        logger: The logger to use.
        level: The logging level.
        rich: Whether to use rich formatting.
        style: The style to use for the logging.
        bg: The background to use for the logging (kept for API consistency).

    Returns:
        The decorated function, a decorator function, or the traced result.
    """

    def _get_logger(name: str) -> Logger:
        """Get or create a logger."""
        if logger is None:
            return create_logger(name=name, level=level, rich=rich)
        elif isinstance(logger, Logger):
            return logger
        else:
            # It's a standard logging.Logger, wrap it
            _logger = create_logger(name=logger.name)
            _logger._logger = logger
            return _logger

    def _log_request_info(
        bound_args: inspect.BoundArguments,
        func_name: str,
        module_name: str,
        _logger: Logger,
    ):
        """Log HTTP request information."""
        if not show_request:
            return

        # Simply log all arguments passed to the function
        args_info = []
        for param_name, param_value in bound_args.arguments.items():
            # Skip None values if requested
            if request_exclude_none and param_value is None:
                continue
            args_info.append(f"{param_name}: {repr(param_value)}")

        if args_info:
            if rich:
                request_msg = f"[{style}]🌐 HTTP Request from {module_name}.{func_name}()[/{style}]"
                request_msg += f"\n  " + "\n  ".join(args_info)
            else:
                request_msg = f"🌐 HTTP Request from {module_name}.{func_name}()"
                request_msg += f"\n  " + "\n  ".join(args_info)

            _logger.log(level, request_msg)

    def _log_response_info(
        result: Any, exec_time: float, func_name: str, module_name: str, _logger: Logger
    ):
        """Log HTTP response information."""
        if not show_response:
            return

        # Skip None responses if requested
        if response_exclude_none and result is None:
            return

        # Simply log the response as a string representation
        result_str = str(result)
        truncated_result = result_str[:500] + ("..." if len(result_str) > 500 else "")

        if rich:
            response_msg = f"[{style}]📥 HTTP Response to {module_name}.{func_name}() [dim](took {exec_time:.3f}s)[/dim][/{style}]"
            response_msg += f"\n  Response: {truncated_result}"
        else:
            response_msg = f"📥 HTTP Response to {module_name}.{func_name}() (took {exec_time:.3f}s)"
            response_msg += f"\n  Response: {truncated_result}"

        _logger.log(level, response_msg)

    def _log_error_info(
        e: Exception,
        exec_time: float,
        func_name: str,
        module_name: str,
        _logger: Logger,
    ):
        """Log HTTP error information."""
        error_style = "bold red" if rich else None
        if rich:
            error_msg = f"[{error_style}]❌ HTTP Error in {module_name}.{func_name}() [dim](after {exec_time:.3f}s)[/dim][/{error_style}]"
            error_msg += f"\n  [red]{type(e).__name__}: {str(e)}[/red]"
        else:
            error_msg = (
                f"❌ HTTP Error in {module_name}.{func_name}() (after {exec_time:.3f}s)"
            )
            error_msg += f"\n  {type(e).__name__}: {str(e)}"

        _logger.error(error_msg)

    def decorator(
        target_fn: Union[Callable[_P, _R], Callable[_P, Awaitable[_R]]],
    ) -> Union[Callable[_P, _R], Callable[_P, Awaitable[_R]]]:
        """Decorator that wraps sync or async functions."""

        if asyncio.iscoroutinefunction(target_fn):
            # Async function
            @wraps(target_fn)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                _logger = _get_logger(
                    f"http.{target_fn.__module__}.{target_fn.__name__}"
                )

                # Get function signature for parameter inspection
                sig = inspect.signature(target_fn)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                func_name = target_fn.__name__
                module_name = target_fn.__module__

                # Log request info
                _log_request_info(bound_args, func_name, module_name, _logger)

                # Track execution time
                start_time = time.time()

                try:
                    # Execute the async function
                    result = await target_fn(*args, **kwargs)

                    # Calculate execution time
                    exec_time = time.time() - start_time

                    # Log response info
                    _log_response_info(
                        result, exec_time, func_name, module_name, _logger
                    )

                    return result

                except Exception as e:
                    # Calculate execution time
                    exec_time = time.time() - start_time

                    # Log error info
                    _log_error_info(e, exec_time, func_name, module_name, _logger)

                    # Re-raise the exception
                    raise

            return async_wrapper
        else:
            # Sync function
            @wraps(target_fn)
            def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                _logger = _get_logger(
                    f"http.{target_fn.__module__}.{target_fn.__name__}"
                )

                # Get function signature for parameter inspection
                sig = inspect.signature(target_fn)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                func_name = target_fn.__name__
                module_name = target_fn.__module__

                # Log request info
                _log_request_info(bound_args, func_name, module_name, _logger)

                # Track execution time
                start_time = time.time()

                try:
                    # Execute the function
                    result = target_fn(*args, **kwargs)

                    # Calculate execution time
                    exec_time = time.time() - start_time

                    # Log response info
                    _log_response_info(
                        result, exec_time, func_name, module_name, _logger
                    )

                    return result

                except Exception as e:
                    # Calculate execution time
                    exec_time = time.time() - start_time

                    # Log error info
                    _log_error_info(e, exec_time, func_name, module_name, _logger)

                    # Re-raise the exception
                    raise

            return sync_wrapper

    # Handle different usage patterns
    if fn_or_call is None:
        # Called with parameters: @trace_http(show_request=False)
        return decorator
    elif callable(fn_or_call):
        # Called directly as decorator: @trace_http
        return decorator(fn_or_call)
    else:
        # Called with a function result: trace_http(some_function(), ...)
        # In this case, we can't trace the function call since it's already executed
        # But we can still log the response
        _logger = _get_logger("http.direct_call")

        if show_response and fn_or_call is not None:
            _log_response_info(fn_or_call, 0.0, "direct_call", "trace_http", _logger)

        return fn_or_call


def install_trace_http(
    *,
    show_request: bool = True,
    show_response: bool = True,
    request_exclude_none: bool = True,
    response_exclude_none: bool = False,
    logger: Union[logging.Logger, Logger, None] = None,
    level: Union[LoggerLevelName, str, int] = "debug",
    rich: bool = True,
    style: Union[CLIStyleType, str] = "white",
    bg: Union[CLIStyleBackgroundType, str] = None,  # noqa: ARG001
    patch_imports: bool = True,
) -> None:
    """Install global HTTP tracing for all HTTP-related functions.

    This function patches common HTTP libraries to automatically trace all
    HTTP requests and responses without needing to manually decorate functions.

    Args:
        show_request: Whether to show the request body.
        show_response: Whether to show the response body.
        request_exclude_none: Whether to exclude None values from request logging.
        response_exclude_none: Whether to exclude None values from response logging.
        logger: The logger to use.
        level: The logging level.
        rich: Whether to use rich formatting.
        style: The style to use for the logging.
        bg: The background to use for the logging (kept for API consistency).
        patch_imports: Whether to also patch the import mechanism for future imports.
    """
    import sys

    # Create a tracer function with the specified settings
    def create_tracer(original_func):
        return trace_http(
            original_func,
            show_request=show_request,
            show_response=show_response,
            request_exclude_none=request_exclude_none,
            response_exclude_none=response_exclude_none,
            logger=logger,
            level=level,
            rich=rich,
            style=style,
            bg=bg,
        )

    # List of common HTTP libraries and their functions to patch
    patches = [
        # requests library
        ("requests", "get"),
        ("requests", "post"),
        ("requests", "put"),
        ("requests", "delete"),
        ("requests", "patch"),
        ("requests", "head"),
        ("requests", "options"),
        ("requests", "request"),
        # httpx library
        ("httpx", "get"),
        ("httpx", "post"),
        ("httpx", "put"),
        ("httpx", "delete"),
        ("httpx", "patch"),
        ("httpx", "head"),
        ("httpx", "options"),
        ("httpx", "request"),
        # urllib3
        ("urllib3", "request"),
        # aiohttp
        ("aiohttp", "request"),
    ]

    patched_functions = []

    for module_name, func_name in patches:
        try:
            # Check if module is already imported
            if module_name in sys.modules:
                module = sys.modules[module_name]

                # Handle nested module paths like "openai.chat.completions"
                if "." in module_name:
                    module_parts = module_name.split(".")
                    for part in module_parts[1:]:
                        if hasattr(module, part):
                            module = getattr(module, part)
                        else:
                            break
                    else:
                        # Successfully navigated to nested module
                        if hasattr(module, func_name):
                            original_func = getattr(module, func_name)
                            traced_func = create_tracer(original_func)
                            setattr(module, func_name, traced_func)
                            patched_functions.append(f"{module_name}.{func_name}")
                else:
                    # Simple module path
                    if hasattr(module, func_name):
                        original_func = getattr(module, func_name)
                        traced_func = create_tracer(original_func)
                        setattr(module, func_name, traced_func)
                        patched_functions.append(f"{module_name}.{func_name}")

                        # Special handling for litellm - also patch litellm.main if available
                        if module_name == "litellm" and "litellm.main" in sys.modules:
                            main_module = sys.modules["litellm.main"]
                            if hasattr(main_module, func_name):
                                setattr(main_module, func_name, traced_func)

            # Also check if the nested module exists in sys.modules for litellm.main case
            elif "." in module_name and module_name in sys.modules:
                module = sys.modules[module_name]
                if hasattr(module, func_name):
                    original_func = getattr(module, func_name)
                    traced_func = create_tracer(original_func)
                    setattr(module, func_name, traced_func)
                    patched_functions.append(f"{module_name}.{func_name}")

                    # If this is litellm.main, also patch the main litellm module
                    if module_name == "litellm.main" and "litellm" in sys.modules:
                        main_litellm = sys.modules["litellm"]
                        if hasattr(main_litellm, func_name):
                            setattr(main_litellm, func_name, traced_func)

        except (ImportError, AttributeError):
            # Module not available or function doesn't exist
            continue

    # Log what was patched
    if patched_functions:
        _logger = (
            logger
            if isinstance(logger, Logger)
            else create_logger(name="http.install_trace", level=level, rich=rich)
        )

        if rich:
            install_msg = f"[{style}]✨ Installed HTTP tracing on {len(patched_functions)} functions[/{style}]"
            install_msg += f"\n  " + "\n  ".join(patched_functions)
        else:
            install_msg = (
                f"✨ Installed HTTP tracing on {len(patched_functions)} functions"
            )
            install_msg += f"\n  " + "\n  ".join(patched_functions)

        _logger.info(install_msg)
    else:
        _logger = (
            logger
            if isinstance(logger, Logger)
            else create_logger(name="http.install_trace", level=level, rich=rich)
        )
        _logger.warning(
            "No HTTP functions found to patch. Import HTTP libraries first."
        )
