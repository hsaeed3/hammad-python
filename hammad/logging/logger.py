"""hammad.logging.logger"""

import logging as _logging
import inspect
from pathlib import Path
from dataclasses import dataclass, field
from typing import (
    Literal,
    TypeAlias,
    Dict,
    Optional,
    Any,
    Union,
    List,
    Callable,
    Iterator,
)
from typing_extensions import TypedDict
from contextlib import contextmanager

from rich import get_console as get_rich_console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    TaskID,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner
from rich.live import Live

from ..cli.styles.types import (
    CLIStyleType,
)
from ..cli.styles.settings import CLIStyleRenderableSettings, CLIStyleBackgroundSettings
from ..cli.animations import (
    animate_spinning,
)

__all__ = (
    "Logger",
    "create_logger",
    "create_logger_level",
    "LoggerConfig",
    "FileConfig",
)


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------


LoggerLevelName: TypeAlias = Literal["debug", "info", "warning", "error", "critical"]
"""Literal type helper for logging levels."""


class LoggerLevelSettings(TypedDict, total=False):
    """Configuration dictionary for the display style of a
    single logging level."""

    title: CLIStyleType | CLIStyleRenderableSettings
    """Either a string tag or style settings for the title output
    of the messages of this level. This includes module name
    and level name."""

    message: CLIStyleType | CLIStyleRenderableSettings
    """Either a string tag or style settings for the message output
    of the messages of this level. This includes the message itself."""

    background: CLIStyleType | CLIStyleBackgroundSettings
    """Either a string tag or style settings for the background output
    of the messages of this level. This includes the message itself."""


class FileConfig(TypedDict, total=False):
    """Configuration for file logging."""

    path: Union[str, Path]
    """Path to the log file."""

    mode: Literal["a", "w"]
    """File mode - 'a' for append, 'w' for write (overwrites)."""

    max_bytes: int
    """Maximum size in bytes before rotation (0 for no rotation)."""

    backup_count: int
    """Number of backup files to keep during rotation."""

    encoding: str
    """File encoding (defaults to 'utf-8')."""

    delay: bool
    """Whether to delay file opening until first write."""

    create_dirs: bool
    """Whether to create parent directories if they don't exist."""


class LoggerConfig(TypedDict, total=False):
    """Complete configuration for Logger initialization."""

    name: str
    """Logger name."""

    level: Union[str, int]
    """Logging level."""

    rich: bool
    """Whether to use rich formatting."""

    display_all: bool
    """Whether to display all log levels."""

    level_styles: Dict[str, LoggerLevelSettings]
    """Custom level styles."""

    file: Union[str, Path, FileConfig]
    """File logging configuration."""

    files: List[Union[str, Path, FileConfig]]
    """Multiple file destinations."""

    format: str
    """Custom log format string."""

    date_format: str
    """Date format for timestamps."""

    json_logs: bool
    """Whether to output structured JSON logs."""

    console: bool
    """Whether to log to console (default True)."""

    handlers: List[_logging.Handler]
    """Additional custom handlers."""


# -----------------------------------------------------------------------------
# Default Level Styles
# -----------------------------------------------------------------------------

DEFAULT_LEVEL_STYLES: Dict[str, LoggerLevelSettings] = {
    "critical": {
        "message": "red bold",
    },
    "error": {
        "message": "red italic",
    },
    "warning": {
        "message": "yellow italic",
    },
    "info": {
        "message": "white",
    },
    "debug": {
        "message": "white italic dim",
    },
}


# -----------------------------------------------------------------------------
# Logging Filter
# -----------------------------------------------------------------------------


class RichLoggerFilter(_logging.Filter):
    """Filter for applying rich styling to log messages based on level."""

    def __init__(self, level_styles: Dict[str, LoggerLevelSettings]):
        super().__init__()
        self.level_styles = level_styles

    def filter(self, record: _logging.LogRecord) -> bool:
        # Get the level name
        level_name = record.levelname.lower()

        # Check if we have custom styling for this level
        if level_name in self.level_styles:
            style_config = self.level_styles[level_name]

            record._hammad_style_config = style_config

        return True


# -----------------------------------------------------------------------------
# Custom Rich Formatter
# -----------------------------------------------------------------------------


class RichLoggerFormatter(_logging.Formatter):
    """Custom formatter that applies rich styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = get_rich_console()

    def formatMessage(self, record: _logging.LogRecord) -> str:
        """Override formatMessage to apply styling to different parts."""
        # Check if we have style configuration
        if hasattr(record, "_hammad_style_config"):
            style_config = record._hammad_style_config

            # Handle title styling (logger name)
            title_style = style_config.get("title", None)
            if title_style:
                if isinstance(title_style, str):
                    # It's a color/style string tag
                    record.name = f"[{title_style}]{record.name}[/{title_style}]"
                elif isinstance(title_style, dict):
                    # It's a CLIStyleRenderableSettings dict
                    style_str = self._build_renderable_style_string(title_style)
                    if style_str:
                        record.name = f"[{style_str}]{record.name}[/{style_str}]"

            # Handle message styling
            message_style = style_config.get("message", None)
            if message_style:
                if isinstance(message_style, str):
                    # It's a color/style string tag
                    record.message = (
                        f"[{message_style}]{record.getMessage()}[/{message_style}]"
                    )
                elif isinstance(message_style, dict):
                    # It's a CLIStyleRenderableSettings dict
                    style_str = self._build_renderable_style_string(message_style)
                    if style_str:
                        record.message = (
                            f"[{style_str}]{record.getMessage()}[/{style_str}]"
                        )
                else:
                    record.message = record.getMessage()
            else:
                record.message = record.getMessage()
        else:
            record.message = record.getMessage()

        # Now format with the styled values
        formatted = self._style._fmt.format(**record.__dict__)
        return formatted if formatted != "None" else ""

    def _build_renderable_style_string(self, style_dict: dict) -> str:
        """Build a rich markup style string from a CLIStyleRenderableSettings dictionary."""
        style_parts = []

        # Handle all the style attributes from CLIStyleRenderableSettings
        for attr in [
            "bold",
            "italic",
            "dim",
            "underline",
            "strike",
            "blink",
            "blink2",
            "reverse",
            "conceal",
            "underline2",
            "frame",
            "encircle",
            "overline",
        ]:
            if style_dict.get(attr):
                style_parts.append(attr)

        return " ".join(style_parts) if style_parts else ""


# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------


@dataclass
class Logger:
    """Flexible logger with rich styling and custom level support."""

    _logger: _logging.Logger = field(init=False)
    """The underlying logging.Logger instance."""

    _level_styles: Dict[str, LoggerLevelSettings] = field(init=False)
    """Custom level styles."""

    _custom_levels: Dict[str, int] = field(init=False)
    """Custom logging levels."""

    _user_level: str = field(init=False)
    """User-specified logging level."""

    def __init__(
        self,
        name: Optional[str] = None,
        level: Optional[Union[LoggerLevelName, int]] = None,
        rich: bool = True,
        display_all: bool = False,
        level_styles: Optional[Dict[str, LoggerLevelSettings]] = None,
        file: Optional[Union[str, Path, FileConfig]] = None,
        files: Optional[List[Union[str, Path, FileConfig]]] = None,
        format: Optional[str] = None,
        date_format: Optional[str] = None,
        json_logs: bool = False,
        console: bool = True,
        handlers: Optional[List[_logging.Handler]] = None,
    ) -> None:
        """
        Initialize a new Logger instance.

        Args:
            name: Name for the logger. If None, defaults to "hammad"
            level: Logging level. If None, defaults to "debug" if display_all else "warning"
            rich: Whether to use rich formatting for output
            display_all: If True, sets effective level to debug to show all messages
            level_styles: Custom level styles to override defaults
            file: Single file configuration for logging
            files: Multiple file configurations for logging
            format: Custom log format string
            date_format: Date format for timestamps
            json_logs: Whether to output structured JSON logs
            console: Whether to log to console (default True)
            handlers: Additional custom handlers to add
        """
        logger_name = name or "hammad"

        # Initialize custom levels dict
        self._custom_levels = {}

        # Initialize level styles with defaults
        self._level_styles = DEFAULT_LEVEL_STYLES.copy()
        if level_styles:
            self._level_styles.update(level_styles)

        # Handle integer levels by converting to string names
        if isinstance(level, int):
            # Map standard logging levels to their names
            int_to_name = {
                _logging.DEBUG: "debug",
                _logging.INFO: "info",
                _logging.WARNING: "warning",
                _logging.ERROR: "error",
                _logging.CRITICAL: "critical",
            }
            level = int_to_name.get(level, "warning")

        self._user_level = level or "warning"

        if display_all:
            effective_level = "debug"
        else:
            effective_level = self._user_level

        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Check if it's a custom level
        if effective_level.lower() in self._custom_levels:
            log_level = self._custom_levels[effective_level.lower()]
        else:
            log_level = level_map.get(effective_level.lower(), _logging.WARNING)

        # Create logger
        self._logger = _logging.getLogger(logger_name)

        # Store configuration
        self._file_config = file
        self._files_config = files or []
        self._format = format
        self._date_format = date_format
        self._json_logs = json_logs
        self._console_enabled = console
        self._rich_enabled = rich

        # Clear any existing handlers
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        # Setup handlers
        self._setup_handlers(log_level)

        # Add custom handlers if provided
        if handlers:
            for handler in handlers:
                self._logger.addHandler(handler)

        self._logger.setLevel(log_level)
        self._logger.propagate = False

    def _setup_handlers(self, log_level: int) -> None:
        """Setup all handlers for the logger."""
        # Console handler
        if self._console_enabled:
            if self._rich_enabled:
                self._setup_rich_handler(log_level)
            else:
                self._setup_standard_handler(log_level)

        # File handlers
        if self._file_config:
            self._setup_file_handler(self._file_config, log_level)

        for file_config in self._files_config:
            self._setup_file_handler(file_config, log_level)

    def _setup_rich_handler(self, log_level: int) -> None:
        """Setup rich handler for the logger."""
        console = get_rich_console()

        handler = RichHandler(
            level=log_level,
            console=console,
            rich_tracebacks=True,
            show_time=self._date_format is not None,
            show_path=False,
            markup=True,
        )

        format_str = self._format or "| [bold]✼ {name}[/bold] - {message}"
        formatter = RichLoggerFormatter(format_str, style="{")

        if self._date_format:
            formatter.datefmt = self._date_format

        handler.setFormatter(formatter)

        # Add our custom filter
        handler.addFilter(RichLoggerFilter(self._level_styles))

        self._logger.addHandler(handler)

    def _setup_standard_handler(self, log_level: int) -> None:
        """Setup standard handler for the logger."""
        handler = _logging.StreamHandler()

        format_str = self._format or "✼  {name} - {levelname} - {message}"
        if self._json_logs:
            formatter = self._create_json_formatter()
        else:
            formatter = _logging.Formatter(format_str, style="{")
            if self._date_format:
                formatter.datefmt = self._date_format

        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        self._logger.addHandler(handler)

    def _setup_file_handler(
        self, file_config: Union[str, Path, FileConfig], log_level: int
    ) -> None:
        """Setup file handler for the logger."""
        import logging.handlers

        # Parse file configuration
        if isinstance(file_config, (str, Path)):
            config: FileConfig = {"path": file_config}
        else:
            config = file_config.copy()

        file_path = Path(config["path"])

        # Create directories if needed
        if config.get("create_dirs", True):
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine handler type
        max_bytes = config.get("max_bytes", 0)
        backup_count = config.get("backup_count", 0)

        if max_bytes > 0:
            # Rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                filename=str(file_path),
                mode=config.get("mode", "a"),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=config.get("encoding", "utf-8"),
                delay=config.get("delay", False),
            )
        else:
            # Regular file handler
            handler = _logging.FileHandler(
                filename=str(file_path),
                mode=config.get("mode", "a"),
                encoding=config.get("encoding", "utf-8"),
                delay=config.get("delay", False),
            )

        # Set formatter
        if self._json_logs:
            formatter = self._create_json_formatter()
        else:
            format_str = self._format or "[{asctime}] {name} - {levelname} - {message}"
            formatter = _logging.Formatter(format_str, style="{")
            if self._date_format:
                formatter.datefmt = self._date_format

        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        self._logger.addHandler(handler)

    def _create_json_formatter(self) -> _logging.Formatter:
        """Create a JSON formatter for structured logging."""
        import json
        import datetime

        class JSONFormatter(_logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.datetime.fromtimestamp(
                        record.created
                    ).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }

                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_entry)

        return JSONFormatter()

    def setLevel(
        self,
        level: Union[LoggerLevelName, int],
    ) -> None:
        """Set the logging level."""
        self._user_level = level
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)

    def add_level(
        self, name: str, value: int, style: Optional[LoggerLevelSettings] = None
    ) -> None:
        """
        Add a custom logging level.

        Args:
            name: Name of the custom level
            value: Numeric value for the level (should be unique)
            style: Optional style settings for the level
        """
        # Add to Python's logging module
        _logging.addLevelName(value, name.upper())

        # Store in our custom levels
        self._custom_levels[name.lower()] = value

        # Add style if provided
        if style:
            self._level_styles[name.lower()] = style

        # Update filters if using rich handler
        for handler in self._logger.handlers:
            if isinstance(handler, RichHandler):
                # Remove old filter and add new one with updated styles
                for f in handler.filters[:]:
                    if isinstance(f, RichLoggerFilter):
                        handler.removeFilter(f)
                handler.addFilter(RichLoggerFilter(self._level_styles))

    @property
    def level(self) -> str:
        """Get the current logging level."""
        return self._user_level

    @level.setter
    def level(self, value: str) -> None:
        """Set the logging level."""
        self._user_level = value

        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Check custom levels
        if value.lower() in self._custom_levels:
            log_level = self._custom_levels[value.lower()]
        else:
            log_level = level_map.get(value.lower(), _logging.WARNING)

        # Update logger level
        self._logger.setLevel(log_level)

        # Update handler levels
        for handler in self._logger.handlers:
            handler.setLevel(log_level)

    # Convenience methods for standard logging levels
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def log(
        self, level: Union[str, int], message: str, *args: Any, **kwargs: Any
    ) -> None:
        """
        Log a message at the specified level.

        Args:
            level: The level to log at (can be standard or custom)
            message: The message to log
            *args: Additional positional arguments for the logger
            **kwargs: Additional keyword arguments for the logger
        """
        # Standard level mapping
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "warning": _logging.WARNING,
            "error": _logging.ERROR,
            "critical": _logging.CRITICAL,
        }

        # Handle integer levels
        if isinstance(level, int):
            # Use the integer level directly
            log_level = level
        else:
            # Check custom levels first
            if level.lower() in self._custom_levels:
                log_level = self._custom_levels[level.lower()]
            else:
                log_level = level_map.get(level.lower(), _logging.WARNING)

        self._logger.log(log_level, message, *args, **kwargs)

    @property
    def name(self) -> str:
        """Get the logger name."""
        return self._logger.name

    @property
    def handlers(self) -> list[_logging.Handler]:
        """Get the logger handlers."""
        return self._logger.handlers

    def get_logger(self) -> _logging.Logger:
        """Get the underlying logging.Logger instance."""
        return self._logger

    @contextmanager
    def track(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        spinner: Optional[str] = None,
        show_progress: bool = True,
        show_time: bool = True,
        transient: bool = False,
    ) -> Iterator[Union[TaskID, Callable[[str], None]]]:
        """Context manager for tracking progress with rich progress bar or spinner.

        Args:
            description: Description of the task being tracked
            total: Total number of steps (if None, uses spinner instead of progress bar)
            spinner: Spinner style to use (if total is None)
            show_progress: Whether to show progress percentage
            show_time: Whether to show time remaining
            transient: Whether to remove the progress display when done

        Yields:
            TaskID for progress updates or callable for spinner text updates

        Examples:
            # Progress bar
            with logger.track("Processing files", total=100) as task:
                for i in range(100):
                    # do work
                    task.advance(1)

            # Spinner
            with logger.track("Loading data") as update:
                # do work
                update("Still loading...")
        """
        console = get_rich_console()

        if total is not None:
            # Use progress bar
            columns = [SpinnerColumn(), TextColumn("{task.description}")]
            if show_progress:
                columns.extend(
                    [BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%"]
                )
            if show_time:
                columns.append(TimeRemainingColumn())

            with Progress(*columns, console=console, transient=transient) as progress:
                task_id = progress.add_task(description, total=total)

                class TaskWrapper:
                    def __init__(self, progress_obj, task_id):
                        self.progress = progress_obj
                        self.task_id = task_id

                    def advance(self, advance: int = 1) -> None:
                        self.progress.advance(self.task_id, advance)

                    def update(self, **kwargs) -> None:
                        self.progress.update(self.task_id, **kwargs)

                yield TaskWrapper(progress, task_id)
        else:
            # Use spinner
            spinner_obj = Spinner(spinner or "dots", text=description)

            with Live(spinner_obj, console=console, transient=transient) as live:

                def update_text(new_text: str) -> None:
                    spinner_obj.text = new_text
                    live.refresh()

                yield update_text

    def trace_function(self, *args, **kwargs):
        """Apply function tracing decorator. Imports from decorators module."""
        from .decorators import trace_function as _trace_function

        return _trace_function(logger=self, *args, **kwargs)

    def trace_cls(self, *args, **kwargs):
        """Apply class tracing decorator. Imports from decorators module."""
        from .decorators import trace_cls as _trace_cls

        return _trace_cls(logger=self, *args, **kwargs)

    def trace(self, *args, **kwargs):
        """Apply universal tracing decorator. Imports from decorators module."""
        from .decorators import trace as _trace

        return _trace(logger=self, *args, **kwargs)

    def animate_spinning(
        self,
        text: str,
        duration: Optional[float] = None,
        frames: Optional[List[str]] = None,
        speed: float = 0.1,
        level: LoggerLevelName = "info",
    ) -> None:
        """Display spinning animation with logging.

        Args:
            text: Text to display with spinner
            duration: Duration to run animation (defaults to 2.0)
            frames: Custom spinner frames
            speed: Speed of animation
            level: Log level to use
        """
        self.log(level, f"Starting: {text}")
        animate_spinning(
            text,
            duration=duration,
            frames=frames,
            speed=speed,
        )
        self.log(level, f"Completed: {text}")

    def add_file(
        self,
        file_config: Union[str, Path, FileConfig],
        level: Optional[Union[str, int]] = None,
    ) -> None:
        """Add a new file handler to the logger.

        Args:
            file_config: File configuration
            level: Optional level for this handler (uses logger level if None)
        """
        handler_level = level or self._logger.level
        if isinstance(handler_level, str):
            level_map = {
                "debug": _logging.DEBUG,
                "info": _logging.INFO,
                "warning": _logging.WARNING,
                "error": _logging.ERROR,
                "critical": _logging.CRITICAL,
            }
            handler_level = level_map.get(handler_level.lower(), _logging.WARNING)

        self._setup_file_handler(file_config, handler_level)

    def remove_handlers(self, handler_types: Optional[List[str]] = None) -> None:
        """Remove handlers from the logger.

        Args:
            handler_types: List of handler type names to remove.
                         If None, removes all handlers.
                         Options: ['file', 'console', 'rich', 'rotating']
        """
        if handler_types is None:
            self._logger.handlers.clear()
            return

        handlers_to_remove = []
        for handler in self._logger.handlers:
            handler_type = type(handler).__name__.lower()

            if any(ht in handler_type for ht in handler_types):
                handlers_to_remove.append(handler)

        for handler in handlers_to_remove:
            self._logger.removeHandler(handler)

    def get_file_paths(self) -> List[Path]:
        """Get all file paths being logged to."""
        file_paths = []

        for handler in self._logger.handlers:
            if hasattr(handler, "baseFilename"):
                file_paths.append(Path(handler.baseFilename))

        return file_paths

    def flush(self) -> None:
        """Flush all handlers."""
        for handler in self._logger.handlers:
            handler.flush()

    def close(self) -> None:
        """Close all handlers and cleanup resources."""
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def create_logger_level(
    name: str,
    level: int,
    color: Optional[str] = None,
    style: Optional[str] = None,
) -> None:
    """
    Create a custom logging level.

    Args:
        name: The name of the logging level (e.g., "TRACE", "SUCCESS")
        level: The numeric level value (should be between existing levels)
        color: Optional color for rich formatting (e.g., "green", "blue")
        style: Optional style for rich formatting (e.g., "bold", "italic")
    """
    # Convert name to uppercase for consistency
    level_name = name.upper()

    # Add the level to the logging module
    _logging.addLevelName(level, level_name)

    # Create a method on the Logger class for this level
    def log_method(self, message, *args, **kwargs):
        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    # Add the method to the standard logging.Logger class
    setattr(_logging.Logger, name.lower(), log_method)

    # Store level info for potential rich formatting
    if hasattr(_logging, "_custom_level_info"):
        _logging._custom_level_info[level] = {
            "name": level_name,
            "color": color,
            "style": style,
        }
    else:
        _logging._custom_level_info = {
            level: {"name": level_name, "color": color, "style": style}
        }


def create_logger(
    name: Optional[str] = None,
    level: Optional[Union[LoggerLevelName, int]] = None,
    rich: bool = True,
    display_all: bool = False,
    levels: Optional[Dict[LoggerLevelName, LoggerLevelSettings]] = None,
    file: Optional[Union[str, Path, FileConfig]] = None,
    files: Optional[List[Union[str, Path, FileConfig]]] = None,
    format: Optional[str] = None,
    date_format: Optional[str] = None,
    json_logs: bool = False,
    console: bool = True,
    handlers: Optional[List[_logging.Handler]] = None,
) -> Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger. If None, uses caller's function name
        level: Logging level. If None, defaults to "debug" if display_all else "warning"
        rich: Whether to use rich formatting for output
        display_all: If True, sets effective level to debug to show all messages
        levels: Custom level styles to override defaults
        file: Single file configuration for logging
        files: Multiple file configurations for logging
        format: Custom log format string
        date_format: Date format for timestamps
        json_logs: Whether to output structured JSON logs
        console: Whether to log to console (default True)
        handlers: Additional custom handlers to add

    Returns:
        A Logger instance with the specified configuration.
    """
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_code.co_name
        else:
            name = "logger"

    return Logger(
        name=name,
        level=level,
        rich=rich,
        display_all=display_all,
        level_styles=levels,
        file=file,
        files=files,
        format=format,
        date_format=date_format,
        json_logs=json_logs,
        console=console,
        handlers=handlers,
    )


# internal logger and helper
_logger = Logger("hammad", level="warning")


def _get_internal_logger(name: str) -> Logger:
    return Logger(name=name, level="warning")
