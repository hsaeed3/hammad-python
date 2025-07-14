"""hammad-python

A vast ecosystem of ('nightly', dont trust literally any interface to stay the same
for more than a few days) resources, utilities and components for building applications
in Python."""

from typing import TYPE_CHECKING
from ._internal import create_getattr_importer as __hammad_importer__


if TYPE_CHECKING:
    from . import types

    # 'builtins'
    from .cache import cached
    from .cli import print, input, animate
    from .genai import (
        BaseGraph,
        plugin,
        action,
        select,
        agent_decorator as agent,
        language_model_decorator as llm,
        run_embedding_model as embedding,
        define_tool as tool,
    )
    from .data.collections import create_collection as collection
    from .formatting.text import convert_to_text as markdown
    from .mcp import launch_mcp_servers
    from .logging import create_logger as logger
    from .service import serve, serve_mcp
    from .web import (
        run_web_search as web_search,
        run_web_request as web_request,
    )

    from ._main import (
        to,
        run,
        fn,
        new,
        read,
        settings,
    )


__all__ = (
    # types
    "types",
    # -- 'builtins'
    "cached",
    "print",
    "animate",
    "input",
    "llm",
    "agent",
    "embedding",
    "tool",
    "markdown",
    "launch_mcp_servers",
    "action",
    "plugin",
    "select",
    "BaseGraph",
    "collection",
    "logger",
    "serve",
    "serve_mcp",
    "web_search",
    "web_request",
    "to",
    "run",
    "fn",
    "new",
    "read",
    "settings",
)


__getattr__ = __hammad_importer__(__all__)


def __dir__() -> list[str]:
    return list(__all__)
