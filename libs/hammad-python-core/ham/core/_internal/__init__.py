"""ham.core._internal

```markdown
Contains core or private level resources that are not meant to be used outside
of this package. These resources are scoped specifically to this package.
```
"""

from ._import_utils import type_checking_importer
from ._logging import (
    debug,
    verbose,
    logger,
    _get_all_ham_loggers,
    _sync_all_ham_loggers,
    get_debug,
    get_verbose,
    set_debug,
    set_verbose,
    get_console,
    warn_deprecated,
    raise_not_installed,
)


__all__ = (
    "warn_deprecated",
    "raise_not_installed",
    "type_checking_importer",
    "debug",
    "verbose",
    "logger",
    "_get_all_ham_loggers",
    "_sync_all_ham_loggers",
    "get_debug",
    "get_verbose",
    "set_debug",
    "set_verbose",
    "get_console",
)
