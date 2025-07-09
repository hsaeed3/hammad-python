"""hammad.data.configurations

Contains the `Configuration` class and related functions for parsing configurations
from various sources.
"""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer

if TYPE_CHECKING:
    from .configuration import (
        Configuration,
        read_configuration_from_file,
        read_configuration_from_url,
        read_configuration_from_os_vars,
        read_configuration_from_os_prefix,
        read_configuration_from_dotenv,
    )


__all__ = (
    "Configuration",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_vars",
    "read_configuration_from_os_prefix",
    "read_configuration_from_dotenv",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
