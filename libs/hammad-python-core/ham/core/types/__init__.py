"""ham.core.types

```markdown
Core type collection within the `hammad-python` ecosystem. This module contains a
very wide collection of both 'static' or just referenced types, as well as full
models with a lot of useful utilities and functionality."""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer


if TYPE_CHECKING:
    from .configuration import Configuration
    from .file import File
    from .text import Text
    from .jsonrpc import (
        JSONRPCRequest,
        JSONRPCNotification,
        JSONRPCResponse,
        JSONRPCError,
        JSONRPCMessage,
    )
    from .multimodal import Image, Audio


__all__ = (
    # ham.core.types.configuration
    "Configuration",
    # ham.core.types.file
    "File",
    # ham.core.types.text
    "Text",
    # ham.core.types.jsonrpc
    "JSONRPCRequest",
    "JSONRPCNotification",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCMessage",
    # ham.core.types.multimodal
    "Image",
    "Audio",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
