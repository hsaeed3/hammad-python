"""hammad.configuration

Contains the `Configuration` class and related functions for parsing configurations
from various sources.
"""

from typing import TYPE_CHECKING
from .._core._utils._import_utils import _auto_create_getattr_loader

if TYPE_CHECKING:
    from .configuration import (
        Configuration,
        get_configuration_from_file,
        get_configuration_from_url,
        get_configuration_from_os_vars,
        get_configuration_from_os_prefix,
        get_configuration_from_dotenv,
    )


__all__ = (
    "Configuration",
    "get_configuration_from_file",
    "get_configuration_from_url",
    "get_configuration_from_os_vars",
    "get_configuration_from_os_prefix",
    "get_configuration_from_dotenv",
)


__getattr__ = _auto_create_getattr_loader(__all__)


def __dir__() -> list[str]:
    return list(__all__)
