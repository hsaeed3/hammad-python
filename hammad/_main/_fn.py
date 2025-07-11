"""hammad._fn

Namespace resource for **DECORATORS** used at the top level
of the `hammad` package."""


class fn:
    """Top level namespace resource for decorators. This can
    be used as `@hammad.fn.cached`, hammad.fn...`. All functions within
    this module are decorators."""

    from ..cache import cached, auto_cached
    from ..genai import define_tool
    from ..logging import trace, trace_cls, trace_function, trace_http
    from ..service import (
        serve,
    )


__all__ = "fn"
