"""ham.core.cli.logs

Contains the following 'builtin' logging methods:

- `log()`
- `log_progress()`
- `log_iterable()`
"""

from __future__ import annotations

import builtins
from typing import (
    Optional,
    IO,
    Any,
    Dict,
    List,
    Union,
    TYPE_CHECKING,
    Callable,
    Iterable,
    Collection,
    TypeVar,
)
from contextlib import contextmanager

if TYPE_CHECKING:
    from rich.console import (
        JustifyMethod,
        OverflowMethod,
        Console,
        RenderableType,
    )
    from rich.panel import PaddingDimensions
    from ..logging.logger import (
        Logger,
        LoggerLevelName,
        LoggerConfig,
        LoggerLevelSettings,
        FileConfig,
    )
    from .styles.types import (
        CLIStyleType,
        CLIStyleBackgroundType,
        CLIStyleColorName,
        CLIStyleBoxName,
    )
    from .styles.settings import (
        CLIStyleRenderableSettings,
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
    )

# Lazy import cache
_IMPORT_CACHE = {}

T = TypeVar("T")


def _get_logger_classes():
    """Lazy import for logger classes"""
    if "logger_classes" not in _IMPORT_CACHE:
        from ..logging.logger import Logger, create_logger, get_logger

        _IMPORT_CACHE["logger_classes"] = (Logger, create_logger, get_logger)
    return _IMPORT_CACHE["logger_classes"]


def _get_alive_progress():
    """Lazy import for alive_progress functions"""
    if "alive_progress" not in _IMPORT_CACHE:
        # Import from the alive_bar module that was shown in the docstring
        try:
            from alive_progress import alive_bar, alive_it

            _IMPORT_CACHE["alive_progress"] = (alive_bar, alive_it)
        except ImportError:
            # Fallback to None if alive_progress is not available
            _IMPORT_CACHE["alive_progress"] = (None, None)
    return _IMPORT_CACHE["alive_progress"]


def _get_style_utils():
    """Lazy import for style utilities"""
    if "style_utils" not in _IMPORT_CACHE:
        from .styles.utils import live_render, style_renderable

        _IMPORT_CACHE["style_utils"] = (live_render, style_renderable)
    return _IMPORT_CACHE["style_utils"]


def log(
    message: Any,
    level: Optional[Union["LoggerLevelName", int]] = None,
    logger: Optional[Union["Logger", str]] = None,
    # Logger configuration
    logger_name: Optional[str] = None,
    logger_level: Optional[Union["LoggerLevelName", int]] = None,
    rich: bool = True,
    display_all: bool = False,
    level_styles: Optional[Dict[str, "LoggerLevelSettings"]] = None,
    file: Optional[Union[str, "FileConfig"]] = None,
    files: Optional[List[Union[str, "FileConfig"]]] = None,
    format: Optional[str] = None,
    date_format: Optional[str] = None,
    json_logs: bool = False,
    console: bool = True,
    handlers: Optional[List[Any]] = None,
    # Style parameters
    style: Optional["CLIStyleType"] = None,
    style_settings: Optional["CLIStyleRenderableSettings"] = None,
    bg: Optional["CLIStyleBackgroundType"] = None,
    bg_settings: Optional["CLIStyleBackgroundSettings"] = None,
    justify: Optional["JustifyMethod"] = None,
    overflow: Optional["OverflowMethod"] = None,
    no_wrap: Optional[bool] = None,
    emoji: Optional[bool] = None,
    markup: Optional[bool] = None,
    highlight: Optional[bool] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    border: Optional["CLIStyleBoxName"] = None,
    padding: Optional["PaddingDimensions"] = None,
    title: Optional[str] = None,
    expand: Optional[bool] = None,
    live: Optional[Union["CLIStyleLiveSettings", int]] = None,
    duration: Optional[float] = None,
    transient: bool = False,
    new_line_start: bool = False,
    rich_brackets: bool = True,
) -> None:
    """
    Stylized logging function that combines logger functionality with rich styling.

    Args:
        message: The message to log
        level: The logging level to use (defaults to "info")
        logger: Existing Logger instance or logger name to use

        # Logger configuration (used if creating new logger)
        logger_name: Name for new logger (defaults to "hammad")
        logger_level: Level for new logger (defaults to "warning")
        rich: Whether to use rich formatting
        display_all: If True, shows all log levels
        level_styles: Custom level styles
        file: Single file configuration
        files: Multiple file configurations
        format: Custom log format string
        date_format: Date format for timestamps
        json_logs: Whether to output structured JSON logs
        console: Whether to log to console
        handlers: Additional custom handlers

        # Style parameters (applied to message styling)
        style: A color or style name to apply to the content
        style_settings: A dictionary of style settings to apply to the content
        bg: A color or box name to apply to the background
        bg_settings: A dictionary of background settings to apply to the content
        justify: Text justification method
        overflow: Text overflow method
        no_wrap: Disable text wrapping
        emoji: Enable/disable emoji rendering
        markup: Enable/disable Rich markup rendering
        highlight: Enable/disable automatic highlighting
        width: Override the width of the output
        height: Override the height of the output
        border: Border style for panel rendering
        padding: Padding dimensions for panel rendering
        title: Title for panel rendering
        expand: Whether to expand panel to full width
        live: Live settings or duration in seconds
        duration: Duration of live renderable
        transient: Whether to clear output after completion
        new_line_start: Start with a new line before printing
        rich_brackets: Enable automatic bracket tagging
    """
    Logger, create_logger, get_logger = _get_logger_classes()

    # Determine the logger to use
    if logger is None:
        # Create a new logger
        log_instance = create_logger(
            name=logger_name,
            level=logger_level,
            rich=rich,
            display_all=display_all,
            levels=level_styles,
            file=file,
            files=files,
            format=format,
            date_format=date_format,
            json_logs=json_logs,
            console=console,
            handlers=handlers,
        )
    elif isinstance(logger, str):
        # Get existing logger by name
        log_instance = get_logger(logger)
        if not isinstance(log_instance, Logger):
            # Wrap with our Logger class
            log_instance = Logger(
                name=logger,
                level=logger_level or "warning",
                rich=rich,
                display_all=display_all,
                level_styles=level_styles,
                file=file,
                files=files,
                format=format,
                date_format=date_format,
                json_logs=json_logs,
                console=console,
                handlers=handlers,
            )
    else:
        # Use provided logger instance
        log_instance = logger

    # Apply styling to the message if any style parameters are provided
    if any(
        [
            style,
            style_settings,
            bg,
            bg_settings,
            live,
            justify,
            overflow,
            no_wrap,
            emoji,
            markup,
            highlight,
            width,
            height,
            border,
            padding,
            title,
            expand,
            transient,
            rich_brackets,
        ]
    ):
        # Import print function from plugins to handle styling
        from .plugins import print as styled_print

        # Use styled print which will display the message with styling
        styled_print(
            message,
            style=style,
            style_settings=style_settings,
            bg=bg,
            bg_settings=bg_settings,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
            width=width,
            height=height,
            border=border,
            padding=padding,
            title=title,
            expand=expand,
            live=live,
            duration=duration,
            transient=transient,
            new_line_start=new_line_start,
            rich_brackets=rich_brackets,
        )
    else:
        # Only log via the logger if no styling is applied
        log_level = level or "info"
        log_instance.log(log_level, str(message))


@contextmanager
def log_progress(
    total: Optional[int] = None,
    *,
    # alive_bar parameters
    calibrate: Optional[int] = None,
    title: Optional[str] = None,
    length: Optional[int] = None,
    max_cols: Optional[int] = None,
    spinner: Optional[Union[str, Any]] = None,
    bar: Optional[Union[str, Any]] = None,
    unknown: Optional[Union[str, Any]] = None,
    theme: Optional[str] = None,
    force_tty: Optional[Union[int, bool]] = None,
    file: Optional[IO] = None,
    disable: bool = False,
    manual: bool = False,
    enrich_print: bool = True,
    enrich_offset: int = 0,
    receipt: bool = True,
    receipt_text: bool = False,
    monitor: Optional[Union[bool, str]] = None,
    elapsed: Optional[Union[bool, str]] = None,
    stats: Optional[Union[bool, str]] = None,
    monitor_end: Optional[Union[bool, str]] = None,
    elapsed_end: Optional[Union[bool, str]] = None,
    stats_end: Optional[Union[bool, str]] = None,
    title_length: int = 0,
    spinner_length: int = 0,
    refresh_secs: int = 0,
    ctrl_c: bool = True,
    dual_line: bool = False,
    unit: str = "it",
    scale: Optional[str] = None,
    precision: int = 1,
    # Logger parameters
    logger: Optional[Union["Logger", str]] = None,
    logger_name: Optional[str] = None,
    logger_level: Optional[Union["LoggerLevelName", int]] = None,
    log_level: Optional[Union["LoggerLevelName", int]] = None,
    rich_logging: bool = True,
    display_all: bool = False,
    level_styles: Optional[Dict[str, "LoggerLevelSettings"]] = None,
    log_file: Optional[Union[str, "FileConfig"]] = None,
    log_files: Optional[List[Union[str, "FileConfig"]]] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    json_logs: bool = False,
    console: bool = True,
    handlers: Optional[List[Any]] = None,
    # Progress logging options
    log_start: bool = True,
    log_finish: bool = True,
    log_start_message: Optional[str] = None,
    log_finish_message: Optional[str] = None,
):
    """
    Context manager for progress tracking using alive_bar with integrated logging.

    Args:
        total: Total number of steps expected

        # alive_bar parameters
        calibrate: Maximum theoretical throughput to calibrate animation speed
        title: Always visible bar title
        length: Number of cols to render the actual bar
        max_cols: Maximum cols to use if not possible to fetch
        spinner: Spinner style to be rendered next to the bar
        bar: Bar style to be rendered in known modes
        unknown: Bar style to be rendered in unknown mode
        theme: Set of matching spinner, bar and unknown
        force_tty: Forces a specific kind of terminal
        file: File object to write to
        disable: If True, completely disables all output
        manual: Set to manually control the bar position
        enrich_print: Enriches print() and logging messages with bar position
        enrich_offset: Offset to apply to enrich_print
        receipt: Prints the nice final receipt
        receipt_text: Set to repeat the last text message in final receipt
        monitor: Configures the monitor widget
        elapsed: Configures the elapsed time widget
        stats: Configures the stats widget
        monitor_end: Configures the monitor widget within final receipt
        elapsed_end: Configures the elapsed time widget within final receipt
        stats_end: Configures the stats widget within final receipt
        title_length: Fixes the title lengths, or 0 for unlimited
        spinner_length: Forces the spinner length, or 0 for natural one
        refresh_secs: Forces the refresh period, 0 for reactive visual feedback
        ctrl_c: If False, disables CTRL+C (captures it)
        dual_line: If True, places the text below the bar
        unit: Any text that labels your entities
        scale: The scaling to apply to units: 'SI', 'IEC', 'SI2'
        precision: How many decimals to display when scaling

        # Logger parameters
        logger: Existing Logger instance or logger name to use
        logger_name: Name for new logger
        logger_level: Level for new logger
        log_level: Level to log messages at (defaults to "info")
        rich_logging: Whether to use rich formatting for logs
        display_all: If True, shows all log levels
        level_styles: Custom level styles
        log_file: Single file configuration for logging
        log_files: Multiple file configurations for logging
        log_format: Custom log format string
        date_format: Date format for timestamps
        json_logs: Whether to output structured JSON logs
        console: Whether to log to console
        handlers: Additional custom handlers

        # Progress logging options
        log_start: Whether to log when progress starts
        log_finish: Whether to log when progress finishes
        log_start_message: Custom message for start log
        log_finish_message: Custom message for finish log

    Yields:
        Progress bar handle for advancing progress

    Examples:
        >>> with log_progress(100, title="Processing") as bar:
        ...     for i in range(100):
        ...         # do work
        ...         bar()

        >>> with log_progress(title="Loading", logger="myapp") as bar:
        ...     # unknown progress
        ...     bar.text = "Still loading..."
    """
    alive_bar, _ = _get_alive_progress()

    if alive_bar is None:
        raise ImportError(
            "alive_progress is required for log_progress. Install with: pip install alive-progress"
        )

    Logger, create_logger, get_logger = _get_logger_classes()

    # Set up logger
    if logger is None:
        log_instance = create_logger(
            name=logger_name,
            level=logger_level,
            rich=rich_logging,
            display_all=display_all,
            levels=level_styles,
            file=log_file,
            files=log_files,
            format=log_format,
            date_format=date_format,
            json_logs=json_logs,
            console=console,
            handlers=handlers,
        )
    elif isinstance(logger, str):
        log_instance = get_logger(logger)
        if not isinstance(log_instance, Logger):
            log_instance = Logger(
                name=logger,
                level=logger_level or "warning",
                rich=rich_logging,
                display_all=display_all,
                level_styles=level_styles,
                file=log_file,
                files=log_files,
                format=log_format,
                date_format=date_format,
                json_logs=json_logs,
                console=console,
                handlers=handlers,
            )
    else:
        log_instance = logger

    # Determine log level
    use_log_level = log_level or "info"

    # Log start message
    if log_start:
        start_msg = log_start_message or f"Starting progress: {title or 'Processing'}"
        if total:
            start_msg += f" (total: {total})"
        log_instance.log(use_log_level, start_msg)

    # Create alive_bar with all parameters
    with alive_bar(
        total,
        calibrate=calibrate,
        title=title,
        length=length,
        max_cols=max_cols,
        spinner=spinner,
        bar=bar,
        unknown=unknown,
        theme=theme,
        force_tty=force_tty,
        file=file,
        disable=disable,
        manual=manual,
        enrich_print=enrich_print,
        enrich_offset=enrich_offset,
        receipt=receipt,
        receipt_text=receipt_text,
        monitor=monitor,
        elapsed=elapsed,
        stats=stats,
        monitor_end=monitor_end,
        elapsed_end=elapsed_end,
        stats_end=stats_end,
        title_length=title_length,
        spinner_length=spinner_length,
        refresh_secs=refresh_secs,
        ctrl_c=ctrl_c,
        dual_line=dual_line,
        unit=unit,
        scale=scale,
        precision=precision,
    ) as bar:
        try:
            yield bar
        finally:
            # Log finish message
            if log_finish:
                finish_msg = (
                    log_finish_message or f"Completed progress: {title or 'Processing'}"
                )
                if hasattr(bar, "current"):
                    finish_msg += f" (processed: {bar.current})"
                log_instance.log(use_log_level, finish_msg)


def log_iterable(
    it: Collection[T],
    total: Optional[int] = None,
    *,
    # alive_it parameters
    finalize: Optional[Callable[[Any], None]] = None,
    calibrate: Optional[int] = None,
    title: Optional[str] = None,
    length: Optional[int] = None,
    max_cols: Optional[int] = None,
    spinner: Optional[Union[str, Any]] = None,
    bar: Optional[Union[str, Any]] = None,
    unknown: Optional[Union[str, Any]] = None,
    theme: Optional[str] = None,
    force_tty: Optional[Union[int, bool]] = None,
    file: Optional[IO] = None,
    disable: bool = False,
    enrich_print: bool = True,
    enrich_offset: int = 0,
    receipt: bool = True,
    receipt_text: bool = False,
    monitor: Optional[Union[bool, str]] = None,
    elapsed: Optional[Union[bool, str]] = None,
    stats: Optional[Union[bool, str]] = None,
    monitor_end: Optional[Union[bool, str]] = None,
    elapsed_end: Optional[Union[bool, str]] = None,
    stats_end: Optional[Union[bool, str]] = None,
    title_length: int = 0,
    spinner_length: int = 0,
    refresh_secs: int = 0,
    ctrl_c: bool = True,
    dual_line: bool = False,
    unit: str = "it",
    scale: Optional[str] = None,
    precision: int = 1,
    # Logger parameters
    logger: Optional[Union["Logger", str]] = None,
    logger_name: Optional[str] = None,
    logger_level: Optional[Union["LoggerLevelName", int]] = None,
    log_level: Optional[Union["LoggerLevelName", int]] = None,
    rich_logging: bool = True,
    display_all: bool = False,
    level_styles: Optional[Dict[str, "LoggerLevelSettings"]] = None,
    log_file: Optional[Union[str, "FileConfig"]] = None,
    log_files: Optional[List[Union[str, "FileConfig"]]] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    json_logs: bool = False,
    console: bool = True,
    handlers: Optional[List[Any]] = None,
    # Iteration logging options
    log_start: bool = True,
    log_finish: bool = True,
    log_start_message: Optional[str] = None,
    log_finish_message: Optional[str] = None,
    log_items: bool = False,
    log_item_level: Optional[Union["LoggerLevelName", int]] = None,
) -> Iterable[T]:
    """
    Iterator adapter with progress tracking using alive_it and integrated logging.

    Args:
        it: The input iterable to be processed
        total: Total number of items (auto-detected if None)

        # alive_it parameters
        finalize: Function to be called when the bar is going to finalize
        calibrate: Maximum theoretical throughput to calibrate animation speed
        title: Always visible bar title
        length: Number of cols to render the actual bar
        max_cols: Maximum cols to use if not possible to fetch
        spinner: Spinner style to be rendered next to the bar
        bar: Bar style to be rendered in known modes
        unknown: Bar style to be rendered in unknown mode
        theme: Set of matching spinner, bar and unknown
        force_tty: Forces a specific kind of terminal
        file: File object to write to
        disable: If True, completely disables all output
        enrich_print: Enriches print() and logging messages with bar position
        enrich_offset: Offset to apply to enrich_print
        receipt: Prints the nice final receipt
        receipt_text: Set to repeat the last text message in final receipt
        monitor: Configures the monitor widget
        elapsed: Configures the elapsed time widget
        stats: Configures the stats widget
        monitor_end: Configures the monitor widget within final receipt
        elapsed_end: Configures the elapsed time widget within final receipt
        stats_end: Configures the stats widget within final receipt
        title_length: Fixes the title lengths, or 0 for unlimited
        spinner_length: Forces the spinner length, or 0 for natural one
        refresh_secs: Forces the refresh period, 0 for reactive visual feedback
        ctrl_c: If False, disables CTRL+C (captures it)
        dual_line: If True, places the text below the bar
        unit: Any text that labels your entities
        scale: The scaling to apply to units: 'SI', 'IEC', 'SI2'
        precision: How many decimals to display when scaling

        # Logger parameters
        logger: Existing Logger instance or logger name to use
        logger_name: Name for new logger
        logger_level: Level for new logger
        log_level: Level to log messages at (defaults to "info")
        rich_logging: Whether to use rich formatting for logs
        display_all: If True, shows all log levels
        level_styles: Custom level styles
        log_file: Single file configuration for logging
        log_files: Multiple file configurations for logging
        log_format: Custom log format string
        date_format: Date format for timestamps
        json_logs: Whether to output structured JSON logs
        console: Whether to log to console
        handlers: Additional custom handlers

        # Iteration logging options
        log_start: Whether to log when iteration starts
        log_finish: Whether to log when iteration finishes
        log_start_message: Custom message for start log
        log_finish_message: Custom message for finish log
        log_items: Whether to log each item during iteration
        log_item_level: Level to log items at (defaults to "debug")

    Returns:
        Iterator that yields items from the original iterable

    Examples:
        >>> items = [1, 2, 3, 4, 5]
        >>> for item in log_iterable(items, title="Processing items"):
        ...     process(item)

        >>> data = fetch_data()
        >>> for record in log_iterable(data, logger="myapp", log_items=True):
        ...     handle_record(record)
    """
    _, alive_it = _get_alive_progress()

    if alive_it is None:
        raise ImportError(
            "alive_progress is required for log_iterable. Install with: pip install alive-progress"
        )

    Logger, create_logger, get_logger = _get_logger_classes()

    # Set up logger
    if logger is None:
        log_instance = create_logger(
            name=logger_name,
            level=logger_level,
            rich=rich_logging,
            display_all=display_all,
            levels=level_styles,
            file=log_file,
            files=log_files,
            format=log_format,
            date_format=date_format,
            json_logs=json_logs,
            console=console,
            handlers=handlers,
        )
    elif isinstance(logger, str):
        log_instance = get_logger(logger)
        if not isinstance(log_instance, Logger):
            log_instance = Logger(
                name=logger,
                level=logger_level or "warning",
                rich=rich_logging,
                display_all=display_all,
                level_styles=level_styles,
                file=log_file,
                files=log_files,
                format=log_format,
                date_format=date_format,
                json_logs=json_logs,
                console=console,
                handlers=handlers,
            )
    else:
        log_instance = logger

    # Determine log levels
    use_log_level = log_level or "info"
    item_log_level = log_item_level or "debug"

    # Log start message
    if log_start:
        start_msg = (
            log_start_message or f"Starting iteration: {title or 'Processing items'}"
        )
        if total:
            start_msg += f" (total: {total})"
        elif hasattr(it, "__len__"):
            start_msg += f" (total: {len(it)})"
        log_instance.log(use_log_level, start_msg)

    # Create custom finalize function that includes logging
    def logging_finalize(bar):
        if finalize:
            finalize(bar)

        if log_finish:
            finish_msg = (
                log_finish_message
                or f"Completed iteration: {title or 'Processing items'}"
            )
            if hasattr(bar, "current"):
                finish_msg += f" (processed: {bar.current})"
            log_instance.log(use_log_level, finish_msg)

    # Create alive_it with all parameters
    progress_iter = alive_it(
        it,
        total=total,
        finalize=logging_finalize,
        calibrate=calibrate,
        title=title,
        length=length,
        max_cols=max_cols,
        spinner=spinner,
        bar=bar,
        unknown=unknown,
        theme=theme,
        force_tty=force_tty,
        file=file,
        disable=disable,
        enrich_print=enrich_print,
        enrich_offset=enrich_offset,
        receipt=receipt,
        receipt_text=receipt_text,
        monitor=monitor,
        elapsed=elapsed,
        stats=stats,
        monitor_end=monitor_end,
        elapsed_end=elapsed_end,
        stats_end=stats_end,
        title_length=title_length,
        spinner_length=spinner_length,
        refresh_secs=refresh_secs,
        ctrl_c=ctrl_c,
        dual_line=dual_line,
        unit=unit,
        scale=scale,
        precision=precision,
    )

    # Wrap the iterator to add item logging if requested
    if log_items:

        def logging_wrapper():
            for i, item in enumerate(progress_iter):
                log_instance.log(item_log_level, f"Processing item {i}: {item}")
                yield item

        return logging_wrapper()
    else:
        return progress_iter


__all__ = ("log", "log_progress", "log_iterable")
