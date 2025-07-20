"""ham.core

```markdown
## `hammad-python-core`

This is the core library for `hammad-python` that provides the core
or foundational functionality for the other resources as well as provides a
collection of resources for public use as well that solve various common
problems and tasks found when building python applications.
```
"""

# TODO:
# might move resources to top level, for now will stay here and fully
# defined

from typing import TYPE_CHECKING
from ._internal import type_checking_importer


if TYPE_CHECKING:
    from ._internal._logging import (
        set_debug as debug,
        set_verbose as verbose,
    )
    from .cache import cached, auto_cached, create_cache, Cache
    from .cli import (
        CLIStyleBackgroundSettings,
        CLIStyleLiveSettings,
        CLIStyleRenderableSettings as CLIStyleSettings,
        print,
        animate,
        input,
        log,
        log_iterable,
        log_progress,
    )
    from .conversion import (
        convert_docstring_to_text,
        convert_to_json_schema,
        convert_to_model,
        convert_to_text,
        convert_type_to_text,
    )
    from .logging import (
        Logger,
        LoggerLevelName,
        LoggerLevelSettings,
        create_logger,
        create_logger_level,
    )
    from .models import (
        Model,
        Field,
        FieldInfo,
        field,
        validator as model_field_validator,
        is_field,
        is_model,
        model_settings,
    )
    from .runtime import (
        run_parallel,
        run_sequentially,
        run_with_retry,
        sequentialize_function,
        parallelize_function,
    )
    from .types import Configuration, File, Audio, Image, Text, JSONRPCMessage


__all__ = (
    # ham.core._internal
    "debug",
    "verbose",
    # ham.core.cache
    "cached",
    "auto_cached",
    "create_cache",
    "Cache",
    # ham.core.cli
    "CLIStyleBackgroundSettings",
    "CLIStyleLiveSettings",
    "CLIStyleSettings",
    "print",
    "animate",
    "input",
    "log",
    "log_iterable",
    "log_progress",
    # ham.core.conversion
    "convert_docstring_to_text",
    "convert_to_json_schema",
    "convert_to_model",
    "convert_to_text",
    "convert_type_to_text",
    # ham.core.logging
    "Logger",
    "LoggerLevelName",
    "LoggerLevelSettings",
    "create_logger",
    "create_logger_level",
    # ham.core.models
    "Model",
    "Field",
    "FieldInfo",
    "field",
    "model_field_validator",
    "is_field",
    "is_model",
    "model_settings",
    # ham.core.runtime
    "run_parallel",
    "run_sequentially",
    "run_with_retry",
    "sequentialize_function",
    "parallelize_function",
    # ham.core.types
    "Configuration",
    "File",
    "Audio",
    "Image",
    "Text",
    "JSONRPCMessage",
)


def __dir__() -> list[str]:
    return list(__all__)


__getattr__ = type_checking_importer(__all__)
