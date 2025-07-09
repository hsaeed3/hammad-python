"""hammad.service

An optional extension to the `hammad-python` package, installable with:

```bash
pip install hammad-python[service]
```

TLDR: FastAPI is already so gosh darn simple, theres no need for server/client
resources within this submodule. This module contains function/decorators for:

- `@serve` - Easily launch functions as a FastAPI endpoint within a quick server.
- `@serve_mcp` - Serve functions as MCP (Model Context Protocol) server tools.
- `create_service` - Launch a FastAPI server from:
    - A function
    - A model-like object
       - Pydantic models
       - Dataclasses
       - `hammad.base.model.Model`
       - msgspec.Struct
"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .create import (
        create_service,
        async_create_service,
    )
    from .decorators import serve, serve_mcp


__all__ = (
    # hammad.service.create
    "create_service",
    "async_create_service",
    # hammad.service.decorators
    "serve",
    "serve_mcp",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the create and decorators modules."""
    return list(__all__)
